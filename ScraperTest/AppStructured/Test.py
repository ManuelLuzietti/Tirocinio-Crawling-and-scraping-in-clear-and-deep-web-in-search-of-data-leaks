from time import sleep
from Crawler import Crawler


def cookiejarTest():
    crawler = Crawler(False,True,debug=True)
    crawler.initializeDrivers()
    crawler.clearCookies()
    crawler.setCookiesInJar("/home/needcaffeine/cookieFile.json")
    crawler.initializeCookies()
    crawler._driver.get("https://naruto.forumcommunity.net/")
    sleep(20)

def manualCookieSetter():
    crawler = Crawler(False,True,debug=True)
    crawler.initializeDrivers()
    crawler.clearCookies()
    crawler.manualCookieJarSetter()
    crawler.initializeDrivers()
    crawler._driver.get("https://naruto.forumcommunity.net/")
    sleep(20)

def getTimeoutTest():
    crawler = Crawler(False,True,debug=True)
    crawler.initializeDrivers() 
    crawler.setGetTimeout(2)
    crawler.setScraperConfig(["https://thehiddenwiki.org/"],regex="[dD]rugs?")
    crawler.start()

def proxyTest():
    crawler = Crawler(False,True,debug=True,proxy="socks5://5.161.86.206:1080")
    crawler.initializeDrivers() 
    crawler._driver.get("https://www.whatsmyip.org/")
    sleep(5)

def googleDorksTest():
    crawler = Crawler(False,True,debug=True)
    crawler.addStartingPageWithDorks("ciao")
    crawler.setScraperConfig([],regex="[Dd]rug")
    crawler.start()

def transversalTimeoutTest():
    crawler = Crawler(False,True,debug=True)
    crawler.initializeDrivers() 
    crawler.setTransversalTimeout(3)
    crawler.setScraperConfig(["https://thehiddenwiki.org/"],regex="[dD]rugs?")
    crawler.start()

testDic = {
    "1" : cookiejarTest,
    "2" : manualCookieSetter,
    "3" : getTimeoutTest,
    "4" : proxyTest,
    "5" : googleDorksTest,
    "6" : transversalTimeoutTest

}

if __name__ == "__main__":
    num = input("insert n. test: ")
    testDic[num]()
    
