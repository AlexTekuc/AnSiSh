 **AnSiSh**
=====================
The AnSiSh (Antiplagiat Simple Shingles) is focused on comparing two documents. 
It is based on the basic shingle algorithm, without using a random sample of 84 possible ones. 
All received checksums are compared. The program only works with .txt, .docx and .pdf files.

To start the program, you need to install the following libraries.

pip install pymupdf
pip install fitz
pip install PySimpleGUI
pip install textract

This program also has the ability to check the replacement of Russian characters in English.
The scroller allows user to select the required sequence of shingles.

If there is a lack or absence of words in the documents, or if the file format is incorrect, a corresponding error will be generated.
