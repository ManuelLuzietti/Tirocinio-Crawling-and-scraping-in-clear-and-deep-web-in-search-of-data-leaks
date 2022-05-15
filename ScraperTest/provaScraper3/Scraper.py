from collections import deque
from click import option
from numpy import extract
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from sqlalchemy import false
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import urllib.parse as up
from collections import deque
import os 
class Scraper():
    _options = None
    _driver = None
    _currentUrl = None
    _soup = None
    _extracted = set()
    _webstack = deque()
    _blockedExt = (".pdf")
    _visitedWebsites = {}
    _visitedLinks = {}
    

    def __init__(self,headless=True,tor=True,useragent="default",debug=False):
        self._options = webdriver.ChromeOptions()
        prefs = {
            #"download_restrictions": 3
            "profile.managed_default_content_settings.images": 2
        }
        self._options.add_experimental_option(
            "prefs", prefs
        )
        if headless:
            self._options.add_argument("--headless")
        if tor:
            self._options.add_argument("--proxy-server=socks5://127.0.0.1:9050")
        if useragent != "default":
            self._options.add_argument('user-agent='+useragent)
        else :
            self._options.add_argument('user-agent= Mozilla/5.0 (X11; Linux x86_64; rv:91.0) Gecko/20100101 Firefox/91.0')
            self._driver = webdriver.Chrome(chrome_options=self._options,service=Service(ChromeDriverManager().install()))
        self._debug = debug
    '''def scrapeUrl(self,url,cssSelector=None,attr=None):
        if url is None:
            return 
        self._currentUrl = url if url[-1]!= "/" else url[:-1]
        links = self._filteredLinks(self._extractLinks(url),self._currentUrl)
        self._extract(cssSelector,attr)'''

        
    def _extractLinks(self,url):
        if url is None:
            return
        if not self._get(url):
            return 
        content = self._driver.page_source
        soup = BeautifulSoup(content,features="html.parser")
        unfilteredLinks = [ a['href'] for a in soup.select("a[href]")]
        return self._filterLinks(unfilteredLinks,url)

    def _filterLinks(self,urls,currentUrl):
        filteredUrls = []
        for url in urls:
            if url.startswith("#"):
                pass
            elif url.startswith("/"):
                if currentUrl.endswith("/"):
                    filteredUrls.append(currentUrl + url[1:])
                else:
                    filteredUrls.append(currentUrl + url)
            elif  url.startswith(currentUrl):
                filteredUrls.append(url)
        urlsNotVisited = []
        for link in filteredUrls:
            if self.checkVisited(link):
                if self._debug:
                    print("skipping already visited: "+link)
                continue
            else:
                urlsNotVisited.append(link)
        return urlsNotVisited
    
    def _get(self,url:str):
        if url.endswith(self._blockedExt):
            if self._debug :
                print("blocked "+url)
            return False
        else:
            self._driver.get(url)
            return True

    def _extract(self,url,cssSelector=None,attr=None):
        if cssSelector == None:
            return 
        if not self._get(url):
            return 
        content = self._driver.page_source
        soup = BeautifulSoup(content,features="html.parser")
        content = soup.select(cssSelector)
        if attr != None:
            try:
                self._extracted.add(self._extracted + [element[attr] for element in content])
            except:
                self._extracted.add(self._extracted + content)    
        else:
            self._extracted = self._extracted | set(content) 

    def getExtracted(self):
        return self._extracted

    def getWebstack(self):
        return self._webstack

    def checkVisited(self,url):
        if url in self._visitedWebsites:
            return True
        else:
            return False

    def _checkVisitedLink(self,url):
        if url in self._visitedLinks:
            return True
        else:
            return False

    def _updateVisited(self,url):
        self._visitedWebsites[url] = None


    def _scrape(self,link,depth,cssSelector=None,attr=None):
        if self._debug:
            print("scraping :"+link+" depth= " + str(depth))
        #estrae contenuto
        if self._checkVisitedLink(link):
            if self._debug:
                print("skipping visited Link: "+link)
            return 
        self._extract(link,cssSelector,attr)
        if depth == 0:
            return 
        #per ogni link estratto
        for v in self._extractLinks(link):
            vparse = up.urlparse(v)
            currentparse = up.urlparse(link)
            #se link è ref fuori dal dominio
            if(vparse.hostname != currentparse.hostname):
                site = vparse[0]+vparse[1]
                #se sito non già in stack da visitare
                if  self._webstack.count(site) == 0:
                    self._webstack.append(site)
            else : 
                #se link interno a dominio vado di scrape
                self._scrape(v,depth-1,cssSelector,attr)

    def pingWebsite(self,site):
        return os.system("ping -c 1 "+site) == 0
    
    def scrapeWebsite(self,website,cssSelector,attr=None,depth=1):
        #if website[-1] == "/":
        #    website = website[:-1]
        if not self.pingWebsite(up.urlparse(website).hostname):
            return 
        self._webstack.append(website)
        while len(self._webstack) != 0:
            next = self._webstack.popleft()
            if self.checkVisited(website):
                if self._debug:
                    print("skip visited website "+website)
                continue
            self._updateVisited(website)
            if self._debug :
                print("scraping website: " + next)
            self._scrape(next,depth,cssSelector,attr)


if __name__ == "__main__":
    scraper = Scraper(debug=True)
    scraper.scrapeWebsite("https://vargiuweb.it","title",depth=1)
    print(scraper.getExtracted())
    #print(up.urlparse("https://ciao.vargiweb.it/").hostname)

