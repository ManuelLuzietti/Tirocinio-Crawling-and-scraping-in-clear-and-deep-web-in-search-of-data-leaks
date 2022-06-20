from requests import request
import websocket 
import json
from Scraper import Scraper
from DBManager import DBManager

class PBScraper():

    _manager = None
    _regexKeys = None

    def __init__(self,db=0,debug=True):
        self.initSocket()
        self._manager = DBManager(db=db)
        with open("AppStructured/keywords.json","r") as f:
            import json
            self._regexKeys = json.loads(f.read())
        self._debug = debug
        self._scraper = Scraper()

    def initSocket(self):
        self.s = websocket.WebSocket()
    
    def connect(self):
        self.s.connect("wss://pastebin-stream.cryto.net/stream")
    
    def subscribe(self):
        req = {
	            "type": "subscribe"
                }
        self.s.send(json.dumps(req))
    
    def receive(self):
        print(self.s.recv())
    
    def closeSocket(self):
        self.s.close()

    def fullBacklog(self):
        req = {
            "type" : "backlog",
            "all" : True
        }
        self.s.send(json.dumps(req))
        res = json.loads(self.s.recv())["results"]
        return res
    
    def scrapeBacklog(self):
        bl = self.fullBacklog()
        print('ok')
        for log in bl:
            self._regexSearch(log['url'],log['contents'])


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
            

if __name__ == "__main__":
    s = PBScraper()
    s.connect()
    s.subscribe()
    s.scrapeBacklog()
    s.closeSocket()