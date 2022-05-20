from collections import deque
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import urllib.parse as up
from collections import deque
import re
import os 
from threading import *
import time
from RepeatTimer import RepeatTimer
class Crawler(Thread):
    _options = None
    _driver = None
    _currentUrl = None
    _soup = None
    _extracted = set()
    _webstack = deque()
    _blockedExt = (".pdf")
    _visitedWebsites = {}
    _visitedLinks = {}
    _leaks = []
    _blockedWebsites = set()
    _timer = None

    def _pause(self):
        self.__flag.clear()
    def _resume(self):
        self.__flag.set()
    def _stop(self):
        self.__flag.clear()
        self.__running.clear()
    def _timerFunc(self):
        if not self._timerFlag.is_set():
            self._timerFlag.set()

    def setTimeoutForRequests(self,interval):
        self._interval = interval
        self._timerFlag = Event()
        self._timer = RepeatTimer(interval,self._timerFunc)
        self._timer.start()
    

    def __init__(self,headless=True,tor=True,useragent="default",debug=False):
        Thread.__init__(self)
        self.__flag = Event()
        self.__flag.set()
        self.__running = Event()
        self.__running.set()

        self._options = webdriver.ChromeOptions()
        #da decommentare:
        prefs = {
            #"download_restrictions": 3
            #"profile.managed_default_content_settings.images": 2 
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
        self._options.add_argument("--enable-javascript")
        self._driver = webdriver.Chrome(chrome_options=self._options,service=Service(ChromeDriverManager().install()))

        self._debug = debug

        
    def _extractLinks(self,url,content):
        if content is None:
            return []
        soup = BeautifulSoup(content,features="html.parser")
        unfilteredLinks = [ a['href'] for a in soup.select("a[href]")]
        #print(unfilteredLinks)#da togliere
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
            elif url.startswith("http") or url.startswith("https"):
                self._webstack.append(url)
                if self._debug :
                    print("aggiunto sito a webstack: "+ url)
                    print("lunghezza webstack: "+str(len(self._webstack)))
            elif not url.startswith("/"):
                if currentUrl.endswith("/"):
                    filteredUrls.append(currentUrl+url)
                else:
                    filteredUrls.append(currentUrl+"/"+url)
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
        if self._timer is not  None:
            self._timerFlag.wait()
            self._timerFlag.clear()
            print("get request")
        try:
            if url.endswith(self._blockedExt):
                if self._debug :
                    print("blocked "+url)
                return False
            else:
                self._driver.get(url)
                return True
        except Exception:
            print("can't resolve "+ url)
    
    def _regexSearch(self,url,content,regex):
        result = re.search(regex,content)
        if result != None:
            self._leaks.append(url)
            if self._debug:
                print("found pattern match in: "+url)


    def _extract(self,url,content,cssSelector=None,attr=None,regex=None):
        if cssSelector == None and regex==None:
            return 
        if re.search("[cC]loud[fF]lare",content) != None:
            self._blockedWebsites.add(url)
            if self._debug:
                print("blocked website by cloudflare: "+url)
            return
        #print(content) #da togliere, mostra sorgente pagina
        if regex!= None:
            self._regexSearch(url,content,regex)
        if cssSelector != None:
            soup = BeautifulSoup(content,features="html.parser")
            content = soup.select(cssSelector)
            if attr != None:
                try:
                    self._extrsacted.add(self._extracted + [element[attr] for element in content])
                except:
                    self._extracted.add(self._extracted + content)    
            else:
                self._extracted = self._extracted | set(content) 

    def getExtracted(self):
        return self._extracted

    def getVisited(self):
        return self._visitedLinks.keys() | self._visitedWebsites.keys()

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

    def _scrape(self,link,depth,cssSelector=None,attr=None,regex=None):
        if not self.__running.is_set():
            return
        self.__flag.wait()
        if self._debug:
            print("scraping :"+link+" depth= " + str(depth))
        #estrae contenuto
        if self._checkVisitedLink(link):
            if self._debug:
                print("skipping visited Link: "+link)
            return 
        if not self._get(link):
            return 
        content = self._driver.page_source
        self._extract(link,content,cssSelector,attr,regex)  
        if depth == 0:
            return 
        #per ogni link estratto
        #print(self._extractLinks(link)) #<-da togliere per vedere link estratti da ogni pagina
        for v in self._extractLinks(link,content):
            if not self.__running.is_set():
                return 
            self.__flag.wait()
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
    
    def crawlWebsite(self,website,cssSelector=None,attr=None,depth=1,regex=None):
        if website[-1] == "/":
            website = website[:-1]
        if not website.endswith(".onion"):
            if not self.pingWebsite(up.urlparse(website).hostname):
                return 
        self._webstack.append(website)
        while len(self._webstack) > 0 and self.__running.is_set():
            self.__flag.wait()
            next = self._webstack.popleft()
            if self.checkVisited(next):
                if self._debug:
                    print("skip visited website "+website)
                continue
            self._updateVisited(next)
            if self._debug :
                print("scraping website: " + next)
            self._scrape(next,depth,cssSelector,attr,regex)
        if self._timer is not None:
            self._timer.cancel()

    def run(self):
        self.scrapeWebsite(self.website,self.cssSelector,self.attr,self.depth,self.regex)
    
    def setScraperConfig(self,website,cssSelector=None,attr=None,depth=1,regex=None):
        self.website = website
        self.cssSelector = cssSelector
        self.attr = self.attr
        self.depth = depth
        self.regex = regex

