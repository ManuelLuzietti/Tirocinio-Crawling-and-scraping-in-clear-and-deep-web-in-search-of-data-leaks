from rx import throw
import twint
import json
import Scraper
import DBManager

class TwitterScraper():
    def __init__(self,debug=False,db=0) :
        self.c = twint.Config()
        self._debug = debug
        self._scraper = Scraper.Scraper()
        self._manager = DBManager.DBManager(db=db)


    def setConfig(self,limit=None):
        self.config = None
        with open("AppStructured/keywords.json","r") as f:
            self.config = json.loads(f.read())
        if self.config is None:
            raise Exception('keywords.json corrupted or not well-formed')
        query = self.config["mainKeywords"][0]
        for i in range(1,len(self.config["mainKeywords"])):
            query += " OR " + self.config["mainKeywords"][i]
        print(query)
        self.c.Search = query
        if limit is not None:
            self.c.Limit = limit
        self.c.Store_json = True
        self.c.Output = "tweetsScraped.json"
        
    def scrape(self):
        with open("tweetsScraped.json","w"):
            pass
        twint.run.Search(self.c)
       
    
    def analyzeScrapedContent(self):
        tws = []
        with open("tweetsScraped.json","r") as f:
            lines = f.readlines()
            tws += [json.loads(line) for line in lines]
        for tweet in tws:
            self._regexSearch(tweet["link"],tweet["tweet"])

    def _regexSearch(self, url, content):
        if len(self.config["companyKeywords"]) != 0:
            for compRe in self.config["companyKeywords"]:
                if self._scraper.regexSearch(content, compRe) != None:
                    self._manager.addLeak(url)
                    if self._debug:
                        print("found pattern match in: "+url)
                    break
        else:
            self._manager.addLeak(url)
            if self._debug:
                print("found pattern match in: "+url)
            



if __name__ == "__main__":
    t = TwitterScraper(True)
    t.setConfig(limit=1000)
    t.scrape()
    t.analyzeScrapedContent()