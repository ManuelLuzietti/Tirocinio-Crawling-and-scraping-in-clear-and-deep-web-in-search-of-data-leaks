from collections import deque
from click import option
from numpy import extract
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import urllib.parse as up
from collections import deque

class Scraper():
    _options = None
    _driver = None
    _currentUrl = None
    _soup = None
    _urls = []
    _extracted = []
    _visitedWebsites = []
    _webstack = deque()
    

    def __init__(self,headless=True,tor=True,useragent="default"):
        self._options = webdriver.ChromeOptions()
        currentScraping = None
        if headless:
            self._options.add_argument("--headless")
        if tor:
            self._options.add_argument("--proxy-server=socks5://127.0.0.1:9050")
        if useragent != "default":
            self._options.add_argument('user-agent='+useragent)
        else :
            self._options.add_argument('user-agent= Mozilla/5.0 (X11; Linux x86_64; rv:91.0) Gecko/20100101 Firefox/91.0')
            self._driver = webdriver.Chrome(options=self._options,service=Service(ChromeDriverManager().install()))


    def scrapeUrl(self,url,cssSelector=None,attr=None):
        if url is None:
            return 
        self._currentUrl = url if url[-1]!= "/" else url[:-1]
        self._extractLinks(url)
        self._filterLinks(self._unfilteredLinks)
        #print(self._extract("title"))
        self._extract(cssSelector,attr)

        
    def _extractLinks(self,url):
        if url is None:
            return
        self._driver.get(url)
        content = self._driver.page_source
        self._soup = BeautifulSoup(content,features="html.parser")
        self._unfilteredLinks = [ a['href'] for a in self._soup.select("a[href]")]

    def _filterLinks(self,urls):
        filteredUrls = []
        for url in urls:
            if url.startswith("#"):
                pass
            elif url.startswith("/") :
                filteredUrls.append(self._currentUrl + url)
            elif  url.startswith(self._currentUrl):
                filteredUrls.append(url)
        self._urls = self._urls + filteredUrls

    def _extract(self,cssSelector=None,attr=None):
        if cssSelector == None:
            return 
        content = self._soup.select(cssSelector)
        if attr != None:
            try:
                self._extracted.append(self._extracted + [element[attr] for element in content])
            except:
                self._extracted.append(self._extracted + content)    
        else:
            self._extracted.append(self._extracted + content)

    def getExtracted(self):
        return self._extracted

    def _scrape(self,link,depth):
        if depth == 0:
            return 
        
    
    def scrapeWebsite(self,website,depth=1):
        self._webstack.append(website)
        while len(self._webstack) != 0:
            next = self._webstack.popleft()
            self._scrape(next,depth)
            #da finire
        



    
    


if __name__ == "__main__":
    scraper = Scraper()
    try:
        scraper.scrapeUrl("https://vargiweb.it/")
    except:
        pass
    #print(scraper._urls)
    #print(up.urlparse("https://ciao.vargiweb.it/").hostname)

