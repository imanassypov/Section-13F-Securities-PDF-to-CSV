#pip3 install requests[security]
#pip3 install bs4
#pip3 install camelot-py opencv-python ghostscript (on windows make sure to install ghostscript separately)

import requests
from bs4 import BeautifulSoup
import PyPDF2
import tabula
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry


from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)


page = requests.get('https://www.oslobors.no/ob_eng/Oslo-Boers/Listing/Shares-equity-certificates-and-rights-to-shares/Oslo-Boers-and-Oslo-Axess/Listed-companies-home-state')

# Create a BeautifulSoup object
soup = BeautifulSoup(page.text, 'html.parser')

#pull all text from 'class-file' div (ctrl+click on element > inspect)
file_list = soup.find(class_='class-file')
file_items = file_list.find_all('a')

#remove garbage at the end of 'class-file'
garbage = soup.find(class_='fa fa-file-pdf-o')
garbage.decompose()

def requests_retry_session(
    retries=3,
    backoff_factor=0.3,
    status_forcelist=(500, 502, 504),
    session=None,
):
    session = session or requests.Session()
    retry = Retry(
        total=retries,
        read=retries,
        connect=retries,
        backoff_factor=backoff_factor,
        status_forcelist=status_forcelist,
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    return session

for f in file_items:
    link = 'https://www.oslobors.no' + f.get('href')
    filename = link.rsplit('/', 1)[-1]
    print ("PDF file link:\t", link)
    print ("PDF filename:\t", filename)
    try:

        r = requests.get(link, allow_redirects=True)
        #r = requests_retry_session().get(link)
        open (filename, 'wb').write(r.content)
        pdfFObj = open (filename, 'rb')
        pdfReader = PyPDF2.PdfFileReader(pdfFObj)
        num_pages = pdfReader.numPages
        start_page = 2
        tabula.convert_into(filename, filename + '.csv', output_format="csv", pages= str(start_page) + '-' + str(num_pages))
        success = True
    except Exception  as e:
        print('exception \t', e)
        continue
