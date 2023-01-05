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
import click
import os, glob
from urllib.parse import urlparse

AREF_HTML = 'https://www.sec.gov/divisions/investment/13flists.htm'
AREF_HTML_LATEST_CLASS = 'blue-chevron'
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
#Treat three consequtive numbers as one column. This will result in spaces being troduced between numbers
PG_COLS=(143.76,163.71,346.4,465.47) #First two divs separate out the cusip into three pieces
# WHEN DEFINIING AREA SWITCH OFF AUTO-DETECTION, IE GUESS=OFF

#START SCANNING FROM PAGE
PG_START_INDEX = 3

#JAVA Options
JAVA_OPTS='-Xmx2G'

#imported table headers
TBL_HEADER=["CUSIP NO","-","ISSUER NAME", "ISSUER DESCRIPTION", "STATUS"]

def is_absolute(url):
    ## Is url absolute or relative
    return bool(urlparse(url).netloc)

def scrub_lis (http_url, selector):
    # Useful section of page is stored in '<div class="article-body">'
    # Files on the page in this class are referenced under unordered lists (html ul element)
    # latest file is also a ul element but with formatting class 'blue-chevron' applied to it
    ## class_elements = soup.find(class_='article-content') will return section of page with all UL's in it
    ## uls = class_elements.find_all('ul') returns list of all UL's objects:
    ## >>> type(lis[0])
    ##<class 'bs4.element.Tag'>

    #match on the report name matching selector
    selector_pattern =''

    if (selector is None):
        #by default grab Current
        selector_pattern=r'Current'
        print ("Report selector not specified, looking for Current...")
    else:
        year,quarter=selector.split('q')
        if (not bool(re.search('\d{4}',year)) & bool(re.search('[1-4]',quarter))):
            print ("specified selector '{SELECTOR}' does not follow [yyyy]q[q] format".format(SELECTOR=selector))
            exit()
        print ("Looking for {YEAR}/{QUARTER}...".format(YEAR=year,QUARTER=quarter))
        selector_pattern=r"{QUARTER}.. quarter {YEAR}".format(QUARTER=quarter, YEAR=year)

    print ('Scrubbing URL:\t{URL}'.format(URL=http_url))
    # retrieve the top index page 
    page = requests.get(http_url)
    # Create a BeautifulSoup object
    soup = BeautifulSoup(page.text, 'html.parser')

    #section of html page defined under 'article-content'
    #which contains list of all UL objects (each UL object has li elements - address and description)
    class_elements = soup.find(class_='article-content')
    #list of all UL objects of type <class 'bs4.element.Tag'>
    uls = []
    uls = class_elements.find_all('ul')

    lis=[]
    #for each group of lists on the page (each UL represents collection of li's per quarter in that year)
    for ul in uls:
        for li in ul.findAll('li'):
            if (bool(re.search(selector_pattern,li.text))):
                lis.append(li)

    #href belongs to 'a' tag: lis[0].a.get('href')
    #textual description: lis[0].text


    # class_elements = soup.find(class_=http_class)
    # arefs = class_elements.find_all('a')
    # return arefs

    return lis

def pdf2df(filename):
    #get number of pages in the specified file
    pdfFObj = open (filename, 'rb')
    pdfReader = PyPDF2.PdfReader(pdfFObj)
    num_pages = len(pdfReader.pages)

    print ("{FILENAME}: extracting pages:{PG_START}-{PG_END}".format(FILENAME=filename,PG_START=PG_START_INDEX, PG_END=num_pages))

    df = tabula.read_pdf(filename,
        pages= str(PG_START_INDEX)+'-'+str(num_pages),
        area=PG_AREA,
        columns=PG_COLS,
        guess=False,
        java_options=JAVA_OPTS,
        multiple_tables=False,
        pandas_options={'names':TBL_HEADER})

    #pop the df out of the list
    df = df[0]

    #delete blank spaces in the first column
    df[TBL_HEADER[0]]=df[TBL_HEADER[0]].str.replace(' ','')

    #last line contains total count as imported from pdf
    expected_row_count = int("".join(re.findall(r'\d',(str(df.iloc[len(df)-1][len(TBL_HEADER)-1])))))
    print ("Expected row count:\t{ROWCOUNT}".format(ROWCOUNT=expected_row_count))

    #drop last row as it is just a note on expected number of entries
    df.drop(df.index[len(df)-1],axis=0,inplace=True)

    extracted_row_count = len(df)
    print ("Extracted row count:\t{ROWCOUNT}".format(ROWCOUNT=extracted_row_count))
    return df


@click.command()
@click.option(
    '--file', '-f',
    help='specify local pdf securities file location')
@click.option(
    '--selector', '-s',
    help='specify year and quarter of the report, ie 2018q4')
@click.option(
    '--dir', '-d',
    help='inner join on each file in specified directory against sec13f report')
@click.option(
    '--on', '-o',
    help='join on column name',
    default='CUSIP - Current')
def main(file,selector,dir,on):
    """
    USE AT YOUR OWN RISK.
    Utility to pull down the list of Section 13(f) securities from
    U.S. Securities and Exchange commission public website.
    List of securities is published in PDF file format on a quarterly basis.
    This utility automates retrieval of the Current List, and converts extracted 
    data in XLSX format
    """

    #disable a pesky warning
    requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

    #list of local panda dataframes to join on the results
    in_dfs =[]

    #Check if inner join is requested on list of local reports
    if (dir is not None):
        if (not os.path.isdir(dir)):
            print ("Input join directory {DNAME} does not exist. Exiting...".format(DNAME=dir))
            quit()
        else:
            exts = ['*.xls', '*.xlsx']
            files = [f for ext in exts for f in glob.glob(os.path.join(dir, ext))]
            in_dfs = [pd.read_excel(f) for f in files]
            print ("Read in {DFS} source reports. Will join on '{ON}' column.".format(DFS=len(in_dfs),ON=on))

    #LOCAL FILE
    if (file is not None):
        #optional file argument was specified
        #check if specified file exists
        if (not os.path.isfile(file)):
            print ("Input file {FNAME} does not exist. Exiting...".format(FNAME=file))
            quit()
        else:
            #local pdf file exists, lets use it
            filename = file
            filename_xlsx = filename+'.xlsx'

            df=pdf2df(filename)
            df.to_excel(filename_xlsx,index=False,header=True)

            i=0
            for left_df in in_dfs:
                print("Inner JOIN '{LEFT}' '{RIGHT}' ON '{ON}'".format(LEFT=files[i],RIGHT=filename,ON=on))
                (left_df.merge(df,left_on=on,right_on=TBL_HEADER[0],how='inner')).to_excel(files[i]+'-'+filename_xlsx,index=False,header=True)
                i=i+1

    #REMOTE FILE
    else:
        #these come in relative format, ie /divisions/investment/13f/13flist2018q4.pdf
        lis = scrub_lis(AREF_HTML, selector)
        for li in lis:
            # get the top level host fqdn address, as all the li elements contain 
            # indirect sub-links to the tld
            p = '(?P<host>http.*://[^:/ ]+).?(?P<port>[0-9]*).*'

            host = re.search(p,AREF_HTML).group('host')

            if (is_absolute(li.a.get('href'))):
                link = li.a.get('href')
            else:
                link = host + li.a.get('href')

            filename = link.rsplit('/', 1)[-1]
            filename_xlsx = filename+'.xlsx'

            print ("---\n{RNAME}: \t{FNAME}".format(RNAME=li.text, FNAME=filename))

            # download report file
            r = requests.get(link, allow_redirects=True)
            open (filename, 'wb').write(r.content)

            df=pdf2df(filename)
            df.to_excel(filename_xlsx,index=False,header=True)

            i=0
            for left_df in in_dfs:
                print("Inner JOIN '{LEFT}' '{RIGHT}' ON '{ON}'".format(LEFT=files[i],RIGHT=filename,ON=on))
                (left_df.merge(df,left_on=on,right_on=TBL_HEADER[0],how='inner')).to_excel(files[i]+'-'+filename_xlsx,index=False,header=True)
                i=i+1

if __name__ == '__main__':
    main()