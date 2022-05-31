from collections import deque
from http import cookiejar
from lib2to3.pgen2 import driver
from multiprocessing.connection import wait
from pickle import FALSE
import traceback
from pendulum import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import urllib.parse as up
from collections import deque
import os 
from threading import *
from RepeatTimer import RepeatTimer
from Scraper import Scraper
from DBManager import DBManager

class Crawler(Thread):
    _options = None
    _driver = None
    _currentUrl = None
    _soup = None
    #_webstack = deque()
    _blockedExt = (".pdf")
    # _visitedWebsites = {} #
    # _visitedLinks = {} #
    # _leaks = [] #
    # _blockedWebsites = set() #
    _timer = None
    _manager = None

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
    


    def __init__(self,headless=True,tor=True,useragent="default",debug=False,db=0):
        Thread.__init__(self)
        self.__flag = Event()
        self.__flag.set()
        self.__running = Event()
        self.__running.set()
        self._scraper = Scraper()

        self._options = webdriver.ChromeOptions()
        #da decommentare:
        prefs = {
            # "download_restrictions": 3,
            # "profile.managed_default_content_settings.images": 2 
        }
        self._options.add_experimental_option(
            "prefs", prefs
        )
        if headless:
            self._options.add_argument("--headless")
      
        if useragent != "default":
            self._options.add_argument('user-agent='+useragent)
        else :
            self._options.add_argument('user-agent= Mozilla/5.0 (X11; Linux x86_64; rv:91.0) Gecko/20100101 Firefox/91.0')
        self._options.add_argument("--enable-javascript")
        #TODO:
        #self._options.add_argument("user-data-dir=/home/needcaffeine/.config/google-chrome")#here user data dir
        #self._options.add_argument("profile-directory=Default")
        

        self._driver = webdriver.Chrome(chrome_options=self._options,service=Service(ChromeDriverManager().install()))
        if tor:
            self._tor = True
            #TODO: 
            #self._options.arguments[-1]= "user-data-dir=/home/needcaffeine/.config/google-chrome/bho"#here user data dir
            #self._options.add_argument("profile-directory=Default2")

            self._options.add_argument("--proxy-server=socks5://127.0.0.1:9050")
            self._driverTor = webdriver.Chrome(chrome_options=self._options,service=Service(ChromeDriverManager().install()))
        else:
            self._tor = False
        self._debug = debug
        self._manager = DBManager(db=db)

        
    def _extractLinks(self,url,content):
        links = self._scraper.getLinks(content)
        return self._filterLinks(links,url)

    #here
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
                #self._webstack.append(url)
                self._manager.addToWebsiteQueue(url)
                if self._debug :
                    print("aggiunto sito a webstack: "+ url)
                    #print("lunghezza webstack: "+str(len(self._webstack)))
            elif not url.startswith("/"):
                if currentUrl.endswith("/"):
                    filteredUrls.append(currentUrl+url)
                else:
                    filteredUrls.append(currentUrl+"/"+url)
        urlsNotVisited = []
        for link in filteredUrls:
            if self._checkVisitedLink(link):
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
                if url.find(".onion") != -1 and self._tor:
                    self._driverTor.get(url)
                    self._lastVisitedPageSource = self._driverTor.page_source
                else:
                    self._driver.get(url)
                    self._lastVisitedPageSource = self._driver.page_source
                return True
        except Exception :
            print("can't resolve "+ url)
            print(traceback.format_exc())

    
    def _regexSearch(self,url,content,regex):
        result = self._scraper.regexSearch(content,regex)
        if result != None:
            # self._leaks.append(url)
            self._manager.addLeak(url)
            if self._debug:
                print("found pattern match in: "+url)


    def _extract(self,url,content,cssSelector=None,attr=None,regex=None):
        if cssSelector == None and regex==None:
            return 
        if self._scraper.regexSearch(content,"[cC]loud[fF]lare") != None:
            #self._blockedWebsites.add(url)
            self._manager.addBlockedWebsite(url)
            if self._debug:
                print("blocked website by cloudflare: "+url)
            return
        if regex!= None:
            self._regexSearch(url,content,regex)
        if cssSelector != None:
            extracted = self._scraper.getContent(content,cssSelector,attr)
            if extracted is not None:
                self._manager.addExtractedContent([x.string for x in extracted])


    def checkVisited(self,url):
        # if url in self._visitedWebsites:
        #     return True
        # else:
        #     return False
        return self._manager.isWebsiteVisited(url)

    def _checkVisitedLink(self,url):
        # if url in self._visitedLinks:
        #     return True
        # else:
        #     return False
        return self._manager.isLinkVisited(url)

    def _updateVisited(self,url):
        # self._visitedWebsites[url] = None
        self._manager.addVisitedWebsite(url)

    def _crawl(self,link,depth,cssSelector=None,attr=None,regex=None):
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
        content = self._lastVisitedPageSource
        self._extract(link,content,cssSelector,attr,regex)  
        if depth == 0:
            return 
        #per ogni link estratto
        #print(self._extractLinks(link)) #<-da togliere per vedere link estratti da ogni pagina
        for v in self._extractLinks(link,content):
            if not self.__running.is_set():
                return 
            self.__flag.wait()
            self._manager.addVisitedLink("link")
            vparse = up.urlparse(v)
            currentparse = up.urlparse(link)
            #se link è ref fuori dal dominio
            if(vparse.hostname != currentparse.hostname):
                site = vparse[0]+vparse[1]
                #se sito non già in stack da visitare
                # if  self._webstack.count(site) == 0:
                #     self._webstack.append(site)
                if not self._manager.isWebsiteInQueue(site):
                    self._manager.addToWebsiteQueue(site)
            else : 
                #se link interno a dominio vado di scrape
                self._crawl(v,depth-1,cssSelector,attr)

    def pingWebsite(self,site):
        return os.system("ping -c 1 "+site) == 0
    
    def crawlWebsite(self,website,cssSelector=None,attr=None,depth=1,regex=None):
        if website[-1] == "/":
            website = website[:-1]
        if not website.endswith(".onion"):
            if not self.pingWebsite(up.urlparse(website).hostname):
                return 
        # self._webstack.append(website)
        self._manager.addToWebsiteQueue(website)
        while not self._manager.isWebsiteQueueEmpty() and self.__running.is_set():
            self.__flag.wait()
            # next = self._webstack.popleft()
            next = self._manager.getFromWebsiteQueue()
            if self.checkVisited(next):
                if self._debug:
                    print("skip visited website "+website)
                continue
            self._updateVisited(next)
            if self._debug :
                print("scraping website: " + next)
            self._crawl(next,depth,cssSelector,attr,regex)
        if self._timer is not None:
            self._timer.cancel()

    def run(self):
        self.crawlWebsite(self.website,self.cssSelector,self.attr,self.depth,self.regex)
    
    def setScraperConfig(self,website,cssSelector=None,attr=None,depth=1,regex=None):
        self.website = website
        self.cssSelector = cssSelector
        self.attr = attr
        self.depth = depth
        self.regex = regex

    def setCookiesInJar(self,cookieFile=None,cookieList=None):
        if cookieFile is None and cookieList is None:
            return 
        cookies = []
        if cookieFile is not None:
            import json
            with open(cookieFile,"r") as f:
                strings = f.read()
            cookies = json.loads(strings)
        if cookieList is not None:
            cookies += cookieList
        self._cookieJar = [cookie for cookie in cookies]

    #una richiesta in più ogni volta che naviga un sito non è il max.
    def getWithCookie(self,url):
        domain = up.urlparse(url).hostname
        cookiesToAdd = []
        for x in self._cookieJar:
            if x["domain"].rfind(domain) != -1:
                cookiesToAdd.append(x)
        if len(cookiesToAdd) != 0:
            self._driver.get(url+"/randomUrl")
            for c in cookiesToAdd:
                self._driver.add_cookie(c)
        self._driver.get(url)
    
    #un po' lento perchè deve aspettare che carichi la pagina.
    def initializeCookies(self,timeout=-1):
        self.setGetTimeout(timeout)
        for cookie in self._cookieJar:
            try:
                self._driver.get("http://"+cookie["domain"])
                self._driver.add_cookie(cookie)
            except:
                print("exception 1")
            #self._driver.implicitly_wait(1)
            if self._tor:
                try:
                    self._driverTor.get("http://"+cookie["domain"])
                    self._driverTor.add_cookie(cookie)
                except:
                    print("exception 2")
                #self._driverTor.implicitly_wait(1)

    def clearCookies(self):
        self._driver.delete_all_cookies()
        if self._tor:
            self._driverTor.delete_all_cookies()
            
    #TODO: vanno messi i vari try catch per usare questo.
    def setGetTimeout(self,seconds=-1):
        crawler._driver.set_page_load_timeout(seconds)
        if self._tor:
            crawler._driverTor.set_page_load_timeout(seconds)


if __name__=="__main__":
    crawler = Crawler(False,True,debug=True)
    
    # crawler._driver.get("chrome://version")
    crawler.setCookiesInJar("/home/needcaffeine/cookieFile.json")
    crawler.clearCookies()
    crawler.initializeCookies()
    crawler._driver.get("https://naruto.forumcommunity.net/")


    



    
    #crawler.setScraperConfig("https://thehiddenwiki.org/",regex="[dD]rugs?",cssSelector="title")
    #print(crawler._driver.get_cookies())

    #crawler.start()