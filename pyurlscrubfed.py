#pip3 install requests[security]
#pip3 install bs4
#pip3 install tabula-py

import requests
from bs4 import BeautifulSoup
import PyPDF2
import tabula
import pandas as pd
from requests.packages.urllib3.exceptions import InsecureRequestWarning
import re 

requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

# TABULA REF: https://github.com/chezou/tabula-py
# PAGE AREA DEFINITION
# OPEN PDF IN PREVIEW IN MAC, USING SQUARE SELECTION & INSPECTOR
# MEASURE TABLE AREA, WHICH WILL BE REPEATED ON EACH PAGE
# LEAVE AMPLE OF SPACE AROUND THE EDGES OF TEXT
# TABULA AREA SPEC:
# y1 = top
# x1 = left
# y2 = top + height
# x2 = left + width
# area=(y1,x1,y2,x2)
PG_LEFT=70
PG_TOP=132
PG_WIDTH=490
# HEIGHT OF 600 will include summary count on the last page
# CAN NOT CUT IT OUT AS IT WILL RESULT IN DATA LOSS ON PREV PAGES
PG_HEIGHT=600

PG_AREA=(PG_TOP,PG_LEFT,PG_TOP+PG_HEIGHT,PG_LEFT+PG_WIDTH)
#COLUMN DIVIDORS, ALSO MEASURE USING OSX PREVIEW
#TABLE OUTER BOUNDARIES ARE NOT TO BE SPECIFIED
#PG_COLS=(111.62,129.81,143.76,163.71,346.4,465.47) #First two divs separate out the cusip into three pieces
PG_COLS=(143.76,163.71,346.4,465.47) #First two divs separate out the cusip into three pieces
# WHEN DEFINIING AREA SWITCH OFF AUTO-DETECTION, IE GUESS=OFF

#START SCANNING FROM PAGE
PG_START_INDEX = 3

#JAVA Options
JAVA_OPTS='-Xmx2G'

#imported table headers
TBL_HEADER=["CUSIP NO","-","ISSUER NAME", "ISSUER DESCRIPTION", "STATUS"]

page = requests.get('https://www.sec.gov/divisions/investment/13flists.htm')

# Create a BeautifulSoup object
soup = BeautifulSoup(page.text, 'html.parser')

#pull all text from 'class-file' div (ctrl+click on element > inspect)
file_list = soup.find(class_='blue-chevron')
file_items = file_list.find_all('a')

#remove garbage at the end of 'class-file'
#garbage = soup.find(class_='fa fa-file-pdf-o')
#garbage.decompose()

start_page = PG_START_INDEX
for f in file_items:
    link = 'https://www.sec.gov' + f.get('href')
    filename = link.rsplit('/', 1)[-1]
    print ("PDF file link:\t", link)
    print ("PDF filename:\t", filename)
    print ("Grabbing file...")
    print (link)
    r = requests.get(link, allow_redirects=True)
    open (filename, 'wb').write(r.content)
    pdfFObj = open (filename, 'rb')
    pdfReader = PyPDF2.PdfFileReader(pdfFObj)
    num_pages = pdfReader.numPages

    print ("Extracting pages:\t", start_page, '-', num_pages)
    #tabula.convert_into(filename, filename + '.csv', output_format="csv", pages= str(start_page) + '-' + str(num_pages),area=PG_AREA,columns=PG_COLS,guess=False,java_options=JAVA_OPTS)
    df = tabula.read_pdf(filename,pages= str(start_page)+'-'+str(num_pages),area=PG_AREA,columns=PG_COLS,guess=False,java_options=JAVA_OPTS,pandas_options={'error_bad_lines':False, 'names':TBL_HEADER})
    #last line contains total count as imported from pdf
    expected_row_count = int("".join(re.findall(r'\d',(str(df.iloc[len(df)-1][len(TBL_HEADER)-1])))))
    print ("Expected row count:\t{ROWCOUNT}".format(ROWCOUNT=expected_row_count))

    #drop last row as it is just a note on expected number of entries
    df.drop(df.index[len(df)-1],axis=0,inplace=True)

    extracted_row_count = len(df)
    print ("Extracted row count:\t{ROWCOUNT}".format(ROWCOUNT=extracted_row_count))

    df.to_excel(filename+'.xlsx',index=False,header=True)
    success = True

