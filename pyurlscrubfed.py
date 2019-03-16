#pip3 install requests[security]
#pip3 install bs4
#pip3 install tabula-py

import requests
from bs4 import BeautifulSoup
import PyPDF2
import tabula


from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)


page = requests.get('https://www.sec.gov/divisions/investment/13flists.htm')

# Create a BeautifulSoup object
soup = BeautifulSoup(page.text, 'html.parser')

#pull all text from 'class-file' div (ctrl+click on element > inspect)
file_list = soup.find(class_='blue-chevron')
file_items = file_list.find_all('a')

#remove garbage at the end of 'class-file'
#garbage = soup.find(class_='fa fa-file-pdf-o')
#garbage.decompose()

start_page = 2
for f in file_items:
    link = 'https://www.sec.gov' + f.get('href')
    filename = link.rsplit('/', 1)[-1]
    print ("PDF file link:\t", link)
    print ("PDF filename:\t", filename)
    try:
        print ("Grabbing file...")
        r = requests.get(link, allow_redirects=True)
        open (filename, 'wb').write(r.content)
        pdfFObj = open (filename, 'rb')
        pdfReader = PyPDF2.PdfFileReader(pdfFObj)
        num_pages = pdfReader.numPages
        print ("Extracting pages:\t", start_page, '-', num_pages)
        tabula.convert_into(filename, filename + '.csv', output_format="csv", pages= str(start_page) + '-' + str(num_pages))
        success = True
    except Exception  as e:
        print('exception \t', e)
