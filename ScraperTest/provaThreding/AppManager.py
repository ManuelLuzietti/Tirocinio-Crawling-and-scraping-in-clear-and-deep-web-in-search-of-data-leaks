from  Scraper import Scraper
from threading import *


class AppManager(Thread,Scraper):
    _website = None
    _cssSelector = None
    _attr = None
    _depth = None
    _regex = None

    def __init__(self,headless=True,tor=True,useragent="default",debug=False):
        Thread.__init__(self)
        Scraper.__init__(headless,tor,useragent,debug)

    def setWebsite(self,website):
        self._website = website

    def setConfig(self,cssSelector=None,attr=None,depth=1,regex=None):
        self._cssSelector = cssSelector
        self._attr = attr
        self._depth = depth
        self._regex = regex

    def run(self):
        self.scrapeWebsite(self._website,self._cssSelector,self._attr,self._depth,self._regex)

if __name__ == "__main__":
    appManager = AppManager(headless= False,tor=False,debug=True)
    appManager.setWebsite("https://vargiuweb.it/")
    appManager.setConfig(regex="semplice")
    appManager.start()
    appManager
