import binascii
import functools
import hashlib
import re
import pathlib
import os
import textract
import time
import PySimpleGUI as sg
import fitz

def check_error(func):

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            func(*args, **kwargs)
        except Exception as e:
            if type(e).__name__ == "FileNotFoundError":
                print("Файл не обнаружен")
            elif type(e).__name__ == "TypeError":
                print("Программа работает только с форматами .txt, .pdf и .docx")
            elif type(e).__name__ == "ZeroDivisionError":
                print("Отсутствуют слова или их недостаточно для применения выбраной последовательности")
            else:
                print(type(e).__name__)

    return wrapper


def get_text(link):

    if link[-3:] == 'txt':
        text_file = open(link, encoding='utf-8')
        text = text_file.read()
        text = text.lower()
        text = re.split(r'\W+', text)
        text.pop()
        text_file.close()
        return text

    if link[-3:] == 'pdf':
        doc = fitz.open(link)
        text = []
        for i in range(doc.pageCount):
            page = doc.load_page(i)
            page_text = page.get_text("text")
            page_text = page_text.lower()
            page_text = re.split(r'\W+', page_text)
            page_text.pop()
            text += page_text
        return text

    if link[-4:] == 'docx':
        text = textract.process(link)
        text = text.decode("utf-8")
        text = text.lower()
        text = re.split(r'\W+', text)
        text.pop()
        return text

def check_grammar(word):

    if len(word) > 2:
        if word[-1] == 's':
            if word[-2] == 'e':
                if word[-3] == 'i':
                    word = word[0:-3] + 'y'
                elif word[-3] == 'y':
                    pass
                else:
                    word = word[0:-2]
            else:
                word = word[0:-1]

    if len(word) > 2:
        if word[-1] == 'о' and (word[-2] == 'н' or word[-2] == 'к'):
            pass
        elif word[-1] == 'ю':
            if word[-2] == 'у':
                word = word[0:-2] + 'ый'
        elif word[-1] == 'е':
            if word[-2] == 'ы':
                word = word[0:-2] + 'ый'
        elif word[-1] == 'и':
            word = word[0:-1]
        elif word[-1] == 'ы':
            word = word[0:-1]
        elif word[-1] == 'а':
            word = word[0:-1]
        elif word[-1] == 'о':
            word = word[0:-1]
    return word

# добавить частицы
def delete_noise(text):

    noises = {'a', 'an', 'the', 'this', 'that',
              'in', 'on', 'at', 'by', 'from',
              'to', 'and', 'but', 'for', 'of', 'or', 'as', 'в',
              'близ', 'вместо', 'за', 'до', 'во', 'для', 'из-за', 'из-под',
              'к', 'ко', 'кроме', 'между', 'на', 'над', 'о', 'от',
              'об', 'обо', 'от', 'ото', 'по', 'под', 'при', 'про',
              'ради', 'с', 'со', 'сквозь', 'среди', 'у', 'через', 'чрез', 'не', 'ни', 'и', 'a'}
    test_text = (word for word in text if word not in noises)
    clear_text = []
    for word in test_text:
        if word in {'is', 'am', 'are', 'was', 'were',
                    'been'}:
            word = 'be'
        word = check_grammar(word)
        clear_text.append(word)

    return clear_text


def check_for_cheating(text, flag=False):

    if flag:
        words_stat = []
        alph = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
        for word in text:
            cnt = 0
            for letter in word:
                if letter in alph:
                    cnt += 1
                    f = letter
            if len(word) > cnt and cnt != 0:
                words_stat.append([word, cnt, f])

            summa = sum([i[1] for i in words_stat])

            if summa > 0:
                print("Была произведена замена на английские символы")
                print("Проблема с буквой", "'", words_stat[0][2], "'",
                "Проверьте ее в документe\nПосле чего выполните проверку вновь\n")
                break

def get_hashed_shingle(text, algorithm, shingle_length):

    shingles_check_sum = []
    for i in range(len(text) - shingle_length + 1):
        shingle = text[i: i + shingle_length]
        string_shingle = ' '.join(shingle)
        if algorithm == 'crc32':
            shingles_check_sum.append(
                binascii.crc32(string_shingle.encode('utf-8')))
        if algorithm == 'sha1':
            hash_object = hashlib.sha1(string_shingle.encode('utf-8'))
            shingles_check_sum.append(hash_object.hexdigest())
        if algorithm == 'md5':
            hash_object = hashlib.md5(string_shingle.encode('utf-8'))
            shingles_check_sum.append(hash_object.hexdigest())
    return shingles_check_sum


@check_error
def compare(links, algorithm, shingle_length, flag):

    shingles = []
    for link in links:
        text = delete_noise(get_text(link))
        check_for_cheating(text, flag=flag)
        shingles_from_text = get_hashed_shingle(text, algorithm=algorithm, shingle_length=shingle_length)
        shingles.append(shingles_from_text)
        count = 0
    for i in range(len(shingles[0])):
        if shingles[0][i] in shingles[1]:
            count += 1

    result = 2 * count / (len(shingles[0]) + len(shingles[1])) * 100
    # print(f" {algorithm}\t  {shingle_length}")
    print(f"Сходство между файлами:: {round(result, 3)}%")
    print("==============================")


@check_error
def main():

    sg.theme('DarkTeal9')

    # ------ Menu Definition ------ #
    menu_def = []

    layout = [
        [sg.Menu(menu_def, tearoff=True)],
        [sg.Frame(size=(396, 125), layout=[
            [sg.Text('Hash функция MD5', font=('Helvetica 12'))],
            [sg.Slider(range=(3, 10), orientation='h', default_value=5,font=('Helvetica 12'), key='slider')],
            [sg.Checkbox('Проверка на замену английскими символами',font=('Helvetica 12'),  key='rus')]],
                  title='', relief=sg.RELIEF_SUNKEN)],
        [sg.Text('Файл '), sg.InputText('Выберите Файл', key='link1'), sg.FileBrowse()],
        [sg.Text('Папка'), sg.InputText('Выберите папку с файлами для сравнения', key ='folder'), sg.FolderBrowse()],
        [sg.Button('Очистить')],
        [sg.Button('Показать файлы в папке')],
        [sg.Output(size=(65, 20),key = '_output_')],
        [sg.Submit('OK'), sg.Cancel('Выход')]]



    window = sg.Window('Антиплагиат', layout, default_element_size=(40, 1))

    # Event Loop
    while True:
        event, values = window.read()
        if event in (None, 'Выйти'):
            break

        if event == ('Показать файлы в папке'):
            if values['folder']:
                for currentFile in pathlib.Path(values['folder']).glob('*.txt'):
                    print(str(currentFile)[len(values['folder']) + 1:])
                for currentFile in pathlib.Path(values['folder']).glob('*.pdf'):
                    print(str(currentFile)[len(values['folder']) + 1:])
                for currentFile in pathlib.Path(values['folder']).glob('*.docx'):
                    print(str(currentFile)[len(values['folder']) + 1:])

        if event == 'OK':
            g = []
            algorithm = []
            algorithm.append('md5')
            all_files = [file for file in os.listdir(values['folder']) if file.endswith(".txt") or file.endswith(".pdf")
                         or file.endswith(".docx")]
            for i in range(len(all_files)):
                g.append(values['folder']+"/"+all_files[i])
                values['link2'] = g[i]
                for alg in algorithm:
                    start_time = time.time()
                    print('Сравниваем с ', all_files[i])
                    compare([values['link1'], values['link2']], flag=values['rus'], algorithm=alg, shingle_length=int(values['slider']))
                    print("--- %s seconds ---" % (time.time() - start_time))


        elif event == 'Выход':
            break
        elif event == 'Очистить':
            window.FindElement('_output_').Update('')

    window.close()

if __name__ == '__main__':
    main()
