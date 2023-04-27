from bs4 import BeautifulSoup
import requests
import urllib3
import logging
import os

urllib3.disable_warnings() #TODO: disabling since this is intranet but we should properly load the site cert or itermediate
logging.basicConfig(filename='crawler.log', encoding='utf-8', level=logging.INFO)

_session = requests.Session()
_pages = dict()
_base = "dump/"

def _save_page(name: str, response: requests.Response):
    
    isExist = os.path.exists(_base + os.path.dirname(name))
    if not isExist:
        os.makedirs(_base + os.path.dirname(name))

    if name.endswith(".pdf"):
        #fn = name if name.endswith(".pdf") else name + ".html"
        with open(file=_base + name, mode="wb") as file:
            file.write(response.content)
    else:
        with open(file=_base + name + ".html", mode="w") as file:
            soup = BeautifulSoup(response.content, 'html.parser', from_encoding="UTF-8")
            div = soup.find_all("div", class_="content")
            if div:
                file.write(div)
            else:
                file.write(response.text)
        

"""
checks if the URI is processable, ignores str if it doesn't start with a /

# Paths (clean URLs)
Disallow: /admin/
Disallow: /comment/reply/
Disallow: /filter/tips
Disallow: /node/add/
Disallow: /search/
Disallow: /user/register
Disallow: /user/password
Disallow: /user/login
Disallow: /user/logout
# Paths (no clean URLs)
Disallow: /index.php/admin/
Disallow: /index.php/comment/reply/
Disallow: /index.php/filter/tips
Disallow: /index.php/node/add/
Disallow: /index.php/search/
Disallow: /index.php/user/password
Disallow: /index.php/user/register
Disallow: /index.php/user/login
Disallow: /index.php/user/logout

TODO: ideally should just directly load and process this: 

robots = _session.get("https://plus.ssc-spc.gc.ca/robots.txt", verify=False).content
logging.debug("robots.txt contents:" + str(robots))

"""
def _process(uri: str) -> bool:
    dnp = ["/index.php/", "/admin/", "/user/", "/search", "/comment/", "/node/", "/filter/"]
    if not uri.startswith('/'):
        return False
    if any(s in uri for s in dnp):
            return False
    return True

"""
Recursively crawl a url and it's given <a> tags in the page.
"""
def _crawl(baseUrl: str, uri: str):
    logging.info("Crawling in ... " + baseUrl + uri)
    r = _session.get(baseUrl + uri, verify=False)

    if r.status_code == 200:
        _pages[baseUrl + uri] = None
        # write to disk ...
        _save_page(uri, r)
        # if not a pdf then go a head and use bs4 to parse the content of it for links ...
        if not uri.endswith(".pdf"):
            soup = BeautifulSoup(r.content, 'html.parser', from_encoding="UTF-8")

            # find links in page and add them to the dictonary
            for link in soup.find_all('a'):
                href = str(link.get('href'))
                ok = _process(href)
                if href and ok:
                    if baseUrl + href not in _pages:
                        # link is valid and has not been processed before, so process it ..
                        logging.info("PROCESSING: " + href)
                        _crawl(baseUrl, href)
                    else:
                        logging.debug("IGNORING: " + href)

# crawl site(s) and retreive a list of URLs and their content
_crawl("https://plus.ssc-spc.gc.ca", "/en")