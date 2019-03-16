import PyPDF2 
#import textract
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
import glob
import os
import sys
import re

topdir = sys.argv[1]

for filename in glob.iglob(os.path.join(topdir, '*.pdf')):
    print (filename)

    #open allows you to read the file
    pdfFileObj = open(filename,'rb')
    #The pdfReader variable is a readable object that will be parsed
    pdfReader = PyPDF2.PdfFileReader(pdfFileObj)
    #discerning the number of pages will allow us to parse through all #the pages
    num_pages = pdfReader.numPages
    count = 0
    text = ""
    #The while loop will read each page
    while count < num_pages:
        pageObj = pdfReader.getPage(count)
        count +=1
        text += pageObj.extractText()

    # get rid of empty lines
    text = "".join([s for s in text.splitlines(True) if s.strip("\r\n")])

    #tricky part of extracting only data fields
    #ASSUMPTION:
    #Look for lines that begin with either digit or cap letter in first position
    #followed by either capital or digit repeating 'n' times
    pattern = r'^[A-Z,0-9][A-Z,0-9]{8}'
    data_str = ""
    data_line_count = 0
    for l in text.splitlines():
        if re.search(pattern, l):
            # DATA CLEANUP
            # ASSUMPTION: FIRST CODE MUST BE "9" CHARS LONG
            # (1.) '*' char gets lumped with adjacent positions
            cleanup_pattern = r'([A-Z,0-9]?)([\*])([A-Z,0-9]?)'
            l = re.sub(cleanup_pattern, r'\1 \2 \3', l)

            # (2.) FIRST AND SECOND DATA FIELD ARE GETTING LUMPED TOGETHER, ie: 000868109ACNB
            # AND AT SAME TIME EXTRA CHAR GETS ADDED IN FIRST POSITION OF FIRST DATA FIELD
            # KILL EXTRA CHAR AND INJECT SPACE
            cleanup_pattern = r'^[0-9]?([A-Z,0-9]{9})([A-Z])'
            l = re.sub(cleanup_pattern, r'\1 \2', l)

            # (2.) EXTRA CHAR GETS CARRIED OVER FROM PREVIOUS PAGE, ie: 4928551AB6VIVUS
            # KILL FIRST CHAR
            #cleanup_pattern = r'^([A-Z,0-9])([A-Z,0-9]{9})'
            #l = re.sub(cleanup_pattern, r'\2', l)

            # (3.) FIRST DATA FIELD GETS LUMPED WITH SECOND DATAFIELD, ie: 98979F107ZOMEDICA
            # SO WE INJECT SPACE BETWEEN FIRST 9 CHARS AND NEXT
            #cleanup_pattern = r'^([A-Z,0-9]{9})([A-Z])'
            #l = re.sub(cleanup_pattern, r'\1 \2', l)

            

            data_str += l + '\n'
            data_line_count += 1
    #This if statement exists to check if the above library returned #words. It's done because PyPDF2 cannot read scanned files.
    ##if text != "":
    ##   text = text
    #If the above returns as False, we run the OCR library textract to #convert scanned/image based PDF files into text
    ##else:
    ##   text = textract.process(filename, method='tesseract', language='eng')
    # Now we have a text variable which contains all the text derived #from our PDF file. Type print(text) to see what it contains. It #likely contains a lot of spaces, possibly junk such as '\n' etc.
    # Now, we will clean our text variable, and return it as a list of keywords.

    with open(filename + '.txt', "w", encoding='utf-8') as out_filename:
        out_filename.write(str(data_str))

    print (data_line_count)