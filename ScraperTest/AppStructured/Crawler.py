from multiprocessing.connection import wait
from pickle import FALSE
from time import sleep
import traceback
from pendulum import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import urllib.parse as up
import os 
from threading import *
from RepeatTimer import RepeatTimer
from Scraper import Scraper
from DBManager import DBManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.keys import Keys

class Crawler(Thread):
    _regexKeys = None
    _options = None
    _driver = None
    _currentUrl = None
    _soup = None
    _driver = None
    _driverTor = None
    #_webstack = deque()
    _blockedExt = (".pdf")
    # _visitedWebsites = {} #
    # _visitedLinks = {} #
    # _leaks = [] #
    # _blockedWebsites = set() #
    _timer = None
    _manager = None
    _transversalTimeout = None
    _blockedPath = []
    _queryTruncation = False

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

    def setTimeoutForRequests(self,interval:int):
        self._interval = interval
        self._timerFlag = Event()
        self._timer = RepeatTimer(interval,self._timerFunc)
        self._timer.start()
    
    def addBlockedPath(self,path:str):
        self._blockedPath.append(path)
    
    def removeBlockedPath(self,path:str):
        if path in self._blockedPath:
            self._blockedPath.remove(path)

    def containsBlockedPath(self,url:str):
        for path in self._blockedPath:
            if url.find(path) != -1:
                return True
        return False
    
    def enableQueryTruncation(self):
        self._queryTruncation = True

    def disableQueryTruncation(self):
        self._queryTruncation = False

    def __init__(self,headless=True,tor=True,useragent="default",debug=False,db=0,proxy=None):
        Thread.__init__(self)
        self.setup(headless,tor,useragent,debug,db,proxy)
    
    def setup(self,headless,tor,useragent,debug,db,proxy):
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
        if proxy is not None:    
            self._options.add_argument(f"--proxy-server={proxy}")
        #TODO:
        self._options.add_argument("user-data-dir=/home/needcaffeine/.config/google-chrome/Profile1")#here user data dir
        self._options.add_argument("profile-directory=Profile")
        

        #self._driver = webdriver.Chrome(chrome_options=self._options,service=Service(ChromeDriverManager().install()))
        
        
        if tor:
            self._tor = True
            self._optionsTor = webdriver.ChromeOptions()
            self._optionsTor.add_experimental_option(
                "prefs",prefs
            )
            if headless:
                self._optionsTor.add_argument("--headless")
      
            if useragent != "default":
                self._optionsTor.add_argument('user-agent='+useragent)
            else :
                self._optionsTor.add_argument('user-agent= Mozilla/5.0 (X11; Linux x86_64; rv:91.0) Gecko/20100101 Firefox/91.0')
            self._optionsTor.add_argument("--enable-javascript")
            #TODO: 
            self._optionsTor.add_argument("user-data-dir=/home/needcaffeine/.config/google-chrome/Profile2")#here user data dir
            self._optionsTor.add_argument("profile-directory=Profile")

            self._optionsTor.add_argument("--proxy-server=socks5://127.0.0.1:9050")

            # self._driverTor = webdriver.Chrome(chrome_options=self._options,service=Service(ChromeDriverManager().install()))
        else:
            self._tor = False
        self._debug = debug
        self._manager = DBManager(db=db)

    def initializeDrivers(self):
        self.closeDrivers()
        self._driver = webdriver.Chrome(chrome_options=self._options,service=Service(ChromeDriverManager().install()))
        if self._tor :
            self._driverTor = webdriver.Chrome(chrome_options=self._optionsTor,service=Service(ChromeDriverManager().install()))
                  
    def _extractLinks(self,url,content):
        links = self._scraper.getLinks(content)
        return self._filterLinks(links,url)

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
                self._manager.addToWebsiteQueue(url)
                if self._debug :
                    print("aggiunto sito a webstack: "+ url)
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
            print("can't resolve or timeout exception on "+ url)
            #print(traceback.format_exc())

    
    def _regexSearch(self,url,content):
        if self._regexKeys is None:
            print("please set scraperConfig or keywords")
            return
        for re in self._regexKeys["mainKeywords"]:
            if self._scraper.regexSearch(content,re)!= None:
                if len(self._regexKeys["companyKeywords"]) != 0:
                    for compRe in self._regexKeys["companyKeywords"]:
                        if self._scraper.regexSearch(content,compRe) != None:
                            self._manager.addLeak(url)
                            if self._debug :
                                print("found pattern match in: "+url)
                            break
                else:
                    self._manager.addLeak(url)
                    if self._debug :
                        print("found pattern match in: "+url)
                    break
        
        # result = self._scraper.regexSearch(content,regex)
        # if result != None:
        #     self._manager.addLeak(url)
        #     if self._debug:
        #         print("found pattern match in: "+url)


    def _extract(self,url,content,cssSelector=None,attr=None,regex:bool=False):
        if cssSelector == None and regex==False:
            return 
        if self._scraper.regexSearch(content,"[cC]loud[fF]lare") != None and self._scraper.regexSearch(content,"one more step") != None:
            self._manager.addBlockedWebsite(url)
            if self._debug:
                print("blocked website by cloudflare(?): "+url)
            #self.manualCookieJarSetter(url)
            #return #<- rimuovere commento quando sistemato bug:
            #BUG: stringa cloudflare da sola non basta, perch matcha link di inclusione cloudflare anche se pagina non viene bloccata.
        if regex!= False:
            self._regexSearch(url,content)
        if cssSelector != None:
            extracted = self._scraper.getContent(content,cssSelector,attr)
            if extracted is not None:
                self._manager.addExtractedContent([x.string for x in extracted])


    def checkVisited(self,url):
        return self._manager.isWebsiteVisited(url)

    def _checkVisitedLink(self,url):
        return self._manager.isLinkVisited(url)

    def _updateVisited(self,url):
        self._manager.addVisitedWebsite(url)

    def _crawl(self,link:str,depth,cssSelector=None,attr=None,regex=False):
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
        if self.containsBlockedPath(link):
            if self._debug:
                print("skipping Link with blocked path: "+link)
            return 

        if not self._get(link):
            return 
        content = self._lastVisitedPageSource
        self._extract(link,content,cssSelector,attr,regex)  
        if depth == 0:
            return 
        #per ogni link estratto
        #print(self._extractLinks(link)) #<-da togliere per vedere link estratti da ogni pagina
        count = 0
        self._manager.addVisitedLink(link)

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
                if not self._manager.isWebsiteInQueue(site):
                    self._manager.addToWebsiteQueue(site)
            else : 
                #se link interno a dominio vado di scrape
                count += 1
                if self._transversalTimeout is not None and count > self._transversalTimeout:
                    if self._debug:
                        print("transversal timeout reached on scraping childs of: " + link)
                    break
                if self._queryTruncation:
                    v = "".join(vparse[1:4])
                self._crawl(v,depth-1,cssSelector,attr,regex)

    def pingWebsite(self,site):
        return os.system("ping -c 1 "+site) == 0
    
    def crawlWebsite(self,websites,cssSelector=None,attr=None,depth=1,regex=False):
        for website in websites:
            if website[-1] == "/":
                website = website[:-1]
            self._manager.addToWebsiteQueue(website)
        # if not website.endswith(".onion"):
        #     if not self.pingWebsite(up.urlparse(website).hostname):
        #         return 
        while not self._manager.isWebsiteQueueEmpty() and self.__running.is_set():
            self.__flag.wait()
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
        self.crawlWebsite(self.websites,self.cssSelector,self.attr,self.depth,self.regex)
    
    def setScraperConfig(self,websites:list = [],cssSelector=None,attr=None,depth=1,regex=False):
        self.websites = websites
        self.cssSelector = cssSelector
        self.attr = attr
        self.depth = depth
        self.regex = regex
        with open("AppStructured/keywords.json","r") as f:
            import json
            self._regexKeys = json.loads(f.read())

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
            if cookie["domain"].rfind(".onion") == -1:
                try:
                    self._driver.get("http://"+cookie["domain"])
                    self._driver.add_cookie(cookie)
                except:
                    print("exception 1")
            #self._driver.implicitly_wait(1)
            elif self._tor:
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
    def setGetTimeout(self,seconds=-1):
        self._driver.set_page_load_timeout(seconds)
        if self._tor:
            self._driverTor.set_page_load_timeout(seconds)

    def setTransversalTimeout(self,nLink:int):
        self._transversalTimeout = nLink

    def manualCookieJarSetter(self,url:str=None):
        self.initializeDrivers() 
        if url != None:
            if url.find(".onion") == -1:
                self._driver.get(url)
            else :
                self._driverTor.get(url)
        WebDriverWait(self._driver,10000).until_not(ff)
        if self._tor:
            WebDriverWait(self._driverTor,10000).until_not(ff)
    
    def closeDrivers(self):
        if self._driver is not None:
            self._driver.quit()
        if self._tor and self._driverTor is not None:
            self._driverTor.quit()
    
    def addStartingPageWithDorks(self,dorks):
        self.initializeDrivers()
        self._driver.get("http://www.google.com/")
        try:
            sleep(1)
            elem = self._driver.find_element_by_name("q")
            sleep(1)
            elem.send_keys(dorks)
            sleep(1)
            elem.send_keys(Keys.RETURN)
            sleep(1)
            self._manager.addToWebsiteQueue(self._driver.current_url)
        except:
            print("input elemet not found in www.google.com")
            return

def ff(driver):
    try:
        driver.get_window_position()
        return True
    except:
        return False


    
if __name__=="__main__":
    crawler = Crawler(False,True,debug=True) #proxy="socks5://5.161.86.206:1080")
    #crawler.manualCookieJarSetter()
    
    
    ####
    # fare test:
    # from KeywordsGenerator import generate
    # generate(["odierne"])
    # crawler.setScraperConfig(["https://vargiuweb.it/"],regex=True)
    # crawler.initializeDrivers()
    # crawler.start()
    ###

    #crawler.initializeDrivers()
    #crawler.addStartingPageWithDorks("ciao")
    # crawler.clearCookies()
    # crawler.closeDrivers()
    # crawler.manualCookieJarSetter()
    # crawler.initializeDrivers()


    # crawler._driver.get("https://naruto.forumcommunity.net/")
    
    #crawler._driver.get("chrome://version")
    #crawler.setCookiesInJar("/home/needcaffeine/cookieFile.json")
    #crawler.initializeCookies()



    #<---
    #crawler.clearCookies()
    # WebDriverWait(crawler._driver,100).until_not(ff) 
    # print("ciao")
    #<---here

    #crawler.initializeCookies()
    #crawler._driver.get("https://naruto.forumcommunity.net/")
    #crawler._get("https://gaogdasona.com")

    



    
    # crawler.setScraperConfig(["https://naruto.forumcommunity.net/"],regex="[dD]rugs?",cssSelector="title")
    # #print(crawler._driver.get_cookies())
    # #crawler.setTransversalTimeout(5)
    # crawler.initializeDrivers()
    # crawler.start()

    #crawler._driver.get("https://www.whatsmyip.org/")
