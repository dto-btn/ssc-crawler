from bs4 import BeautifulSoup
import requests
import urllib3
import logging
import os
import re
import base64
import zlib
import urllib.parse
import io
from lxml import etree
import asyncio
from pyppeteer import launch
import undetected_chromedriver as uc
from selenium.webdriver.remote.webdriver import By
import time

urllib3.disable_warnings() #TODO: disabling since this is intranet but we should properly load the site cert or itermediate
logging.basicConfig(filename='crawler.log', encoding='utf-8', level=logging.INFO)

_session = requests.Session()
_pages = dict()
_base = "dump/"

"""
trigger waf SAML flow for this session ...

SAML decoding stuff taken from https://github.com/cwaldbieser/saml_request_decoder

NOTE: dropping this feature as I now need to sign the SAMLResponse and I didn't want to get into that part.
"""
def _wafwaf(session: requests.Session):
    cookies = {}
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36'
    }
    # troubleshooot f5 / microsoft SAML auth WAF
    # this should land on a 200 OK page with JS on it to POST to a URL to finish the SAML authentication and satisfy the F5
    resp = session.get("https://plus.ssc-spc.gc.ca/en", verify=False, headers=headers)
    if resp.status_code == 200:

        # debug what we have here
        print("###################################\n\n\n")
        #print(resp.content)
        print("###################################\n\n\n")

        soup = BeautifulSoup(resp.content, 'html.parser', from_encoding="UTF-8")
        post = ""
        for script in soup.findAll("script"):
            r = re.search('"urlPost":"([-a-zA-Z0-9@:%._\+~#=\/?\\\\]*)', script.text)
            if r:
                post = r.group(1)
                post = post.replace('\\u0026', '&')
                print(post)
                r = session.post("https://login.microsoftonline.com" + post, verify=False, headers=headers)
                print(r)
                break
        if post:
            post = post.replace('\\u0026', '&')
            p = urllib.parse.urlparse(post)
            qs = urllib.parse.parse_qsl(p.query)
            l = [v for k, v in qs if k.lower() == "samlrequest"]
            v = l[0]
            #print(v)
            xml = zlib.decompress(base64.b64decode(v), -15).decode('utf-8')
            buf = io.BytesIO(xml.encode('utf-8'))
            doc = etree.parse(buf)
            #print(etree.tostring(doc.getroot(), pretty_print=True).decode('utf-8'))
        #if post:
        #    logging.debug("got POST, data from js script: " + post)
        #    r = session.post("https://login.microsoftonline.com" + post)
        #    print(r.content)


def _save_page(name: str, response: requests.Response):
    
    isExist = os.path.exists(_base + os.path.dirname(name))
    if not isExist:
        os.makedirs(_base + os.path.dirname(name))

    if name.endswith(".pdf"):
        #fn = name if name.endswith(".pdf") else name + ".html"
        with open(file=_base + name, mode="wb") as file:
            file.write(response.content)
    else:
        #with open(file=_base + name + ".html", mode="w") as file:
        #    file.write(response.content)
        with open(file=_base + name + ".txt", mode="w") as file:
            soup = BeautifulSoup(response.content, 'html.parser', from_encoding="UTF-8")
            for div in soup.find_all("div.content"):
                file.write(div.text)
        
        

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
    _pages[baseUrl + uri] = None #mark this as visited even if the following requests fails
    logging.info("Scanned pages count is: " + str(len(_pages)))

    if r.status_code == 200:    
        # write to disk ...
        _save_page(uri, r)
        # if not a pdf then go a head and use bs4 to parse the content of it for links ...
        if not uri.endswith(".pdf"):
            soup = BeautifulSoup(r.content, 'html.parser', from_encoding="UTF-8")

            # find links in page and add them to the dictonary
            for link in soup.find_all('a'):
                href = str(link.get('href'))
                ok = _process(href) # are we allowed to crawl this space?
                if href and ok:
                    if baseUrl + href not in _pages:
                        # link is valid and has not been processed before, so process it ..
                        logging.info("PROCESSING: " + href)
                        _crawl(baseUrl, href)
                    else:
                        logging.debug("IGNORING: " + href)

#_wafwaf(_session)
# crawl site(s) and retreive a list of URLs and their content
_crawl("https://plus.ssc-spc.gc.ca", "/en")

async def get_html():
    browser = await launch(headless=True, executablePath="/usr/bin/google-chrome-stable")
    page = await browser.newPage()
    await page.setJavaScriptEnabled(True)
    await page.goto("https://plus.ssc-spc.gc.ca/en")
    #await page.waitForSelector("div.content", visible=True)
    await page.waitForNavigation({"waitUntil":"networkidle2"})
    print("network is idle ok ?")
    #res = await page.evaluate(pageFunction='document.querySelector(".button_primary").click();', force_expr=True)
    #<form action="https://login.microsoftonline.com/d05bc194-94bf-4ad6-ae2e-1db0f2e38f5e/login" autocomplete="off" class="provide-min-height" 
    # data-bind="autoSubmit: forceSubmit, attr: { action: postUrl }, ariaHidden: !!activeDialog(),
    #  css: { 'provide-min-height': svr.fUseMinHeight }" id="i0281" method="post" name="f1" novalidate="novalidate" spellcheck="false" target="_top">
    res = await page.evaluate(pageFunction='document.querySelector("form[name=\'f1\']").submit();', force_expr=True)
    #await page.waitForNavigation()
    print(res)
    html = await page.content() # SAML Post ...

    await browser.close()
    return html

#html = asyncio.get_event_loop().run_until_complete(get_html())
#soup = BeautifulSoup(html, "html.parser")

#for input in soup.findAll("input"):
#    print(input)

print("#################################\n#############################################\n###########################################\n")

#for input in soup.findAll("form"):
#    print(input)

#driver = uc.Chrome()
#driver._web_element_cls = uc.UCWebElement
#driver.get("https://plus.ssc-spc.gc.ca/en")
#driver.
#print(driver.current_url)

#time.sleep(5)

#print(driver.current_url)
#results_container = driver.find_element(By.TAG_NAME, "section")
#print(results_container)
#for item in results_container:
#    print(item)

#print(soup)