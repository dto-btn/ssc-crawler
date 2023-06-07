from bs4 import BeautifulSoup
import requests
import urllib3
import logging
import os
from dotenv import load_dotenv
from urllib.parse import urlparse, urlsplit, urlunparse
import msal

load_dotenv()

username = os.environ["USERNAME"]
password = os.environ["PASSWORD"]

urllib3.disable_warnings() #TODO: disabling since this is intranet but we should properly load the site cert or itermediate
logging.basicConfig(filename='crawler.log', encoding='utf-8', level=logging.DEBUG)

_session = requests.Session()
_visited = set()
_base = "dump/"

_blacklist = ["download", "pdf", "docx", "pdf", "canadasite"]
_whitelist = ["/agreements-conventions", "/sites/VF-LFDF"]

def _save_page(name: str, response: requests.Response):
    uri = urlparse(name).path
    if not urlparse(name).query == "":
        uri += "?" + urlparse(name).query
    name = uri
    isExist = os.path.exists(_base + os.path.dirname(name))
    if not isExist:
        os.makedirs(_base + os.path.dirname(name))

    if name.endswith(".pdf"):
        #fn = name if name.endswith(".pdf") else name + ".html"
        with open(file=_base + name, mode="wb") as file:
            file.write(response.content)
    else:
        if not name.endswith(".html"):
             name = name + ".html"
        logging.info("writting file .." + _base + name)
        with open(file=_base + name, mode="wb") as file:
            file.write(response.content)
        

def _process(uri: str) -> bool:
    # ignore anchors ..
    if uri.startswith("#"):
         return False
    
    if any(s in uri for s in _blacklist):
            return False
    
    if any(s in uri for s in _whitelist):
            return True
    
    return False

"""
Recursively crawl a url and it's given <a> tags in the page.
"""
def _crawl(url: str):
        
    _visited.add(url) #mark this as visited even if the following requests fails
    s_url = urlsplit(url)

    uri = s_url.path
    if not s_url.query == "":
        uri += "?" + s_url.query
    
    basepath = url.rsplit("/", 1)[0]
    process = _process(uri)
    logging.debug(f"shall we process this URI? --> {uri} --> {process}")
    if process:
        logging.info(f"Crawling in: {url} and page scanned count = {len(_visited)}") 
        r = _session.get(url, verify=False,allow_redirects=True)
        print(r.url)
        if r.status_code == 200:
            _save_page(url, r)
            soup = BeautifulSoup(r.content, 'html.parser', from_encoding="UTF-8")
            for link in soup.find_all('a'): 
                href = str(link.get('href'))

                if href.startswith("#"):
                       href = _defaultsite + s_url.path + href                     
                elif href.startswith("/"):
                    href = basepath + href
                elif not href.startswith("http"):
                    href = basepath + "/" + href

                if href not in _visited:
                    _crawl(href)
    else:
         logging.debug(f"ignoring: {url} and page scanned count = {len(_visited)}") 

# tbs agreements ...
_defaultsite = "https://www.tbs-sct.canada.ca"
_crawl("https://www.tbs-sct.canada.ca/agreements-conventions/list-eng.aspx")
_crawl("https://www.tbs-sct.canada.ca/agreements-conventions/list-fra.aspx")

# Vendor Tool (sharepoint)
#cache = msal.SerializableTokenCache()
#_session.["token_cache"] = cache.serialize()
#msal_app = msal.PublicClientApplication(client_id=None, authority="https://login.microsoftonline.com/d05bc194-94bf-4ad6-ae2e-1db0f2e38f5e/")
#scopes = ["https://163gc.sharepoint.com/.default"]
#r = msal_app.acquire_token_interactive()


#_defaultsite = "https://163gc.sharepoint.com"
#_crawl("https://163gc.sharepoint.com/sites/VF-LFDF/SitePages/Home.aspx")
#_crawl("https://163gc.sharepoint.com/sites/VF-LFDF/SitePages/fr/Home.aspx")
