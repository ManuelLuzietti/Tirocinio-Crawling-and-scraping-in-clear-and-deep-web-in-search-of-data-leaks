import redis

class DBManager:

    def __init__(self,host="localhost",port="6379",db=0,password=None):
        self._db = redis.Redis(host,port,db,password)

    def addVisitedWebsite(self,website:str):
         return self._db.sadd("visitedWebsites", website)
    
    def isWebsiteVisited(self,website:str):
        return self._db.sismember("visitedWebsites",website) == 1
    
    def addVisitedLink(self,link:str):
        return self._db.sadd("visitedLink",link)
    
    def isLinkVisited(self,link:str):
        return self._db.sismember("visitedLink",link)
    
    def getVisited(self):
        return self._byteSetToStringSet(self._db.sunion(["visitedLink","visitedWebsites"]))
    
    def _byteSetToStringSet(self,set):
        return {elem.decode("utf-8") for elem in set}
    
    def addLeak(self,url:str):
        return self._db.sadd("leakSources",url)
    
    def getLeakSources(self):
        return self._byteSetToStringSet(self._db.smembers("leakSources"))
    
    def addBlockedWebsite(self, website):
        return self._db.sadd("blockedWebsites",website)
    
    def getBlockedWebsites(self):
        return self._byteSetToStringSet(self._db.smembers("blockedWebsites"))
    
    
    def addExtractedContent(self,contentIterable):
        for i in contentIterable:
            self._db.sadd("extractedContent",i)
    
    def getExtractedContent(self):
        return self._byteSetToStringSet(self._db.smembers("extractedContent"))

    def addToWebsiteQueue(self,website):
        return self._db.rpush("websiteQueue",website)

    def getFromWebsiteQueue(self):
        value =  self._db.lpop("websiteQueue")
        if value is None:
            return value
        else:
            return value.decode("utf-8")



if __name__ == "__main__":
    manager = DBManager()
    manager.addVisitedLink("ciao.com")
    print(manager.getVisited())
    print(manager.isLinkVisited("ciao.com"))