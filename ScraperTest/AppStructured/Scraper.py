from bs4 import BeautifulSoup
import re

class Scraper:
    def __init__(self):
        pass
    def getLinks(self,content):
        if content is None:
            return []
        soup = BeautifulSoup(content,features="html.parser")
        unfilteredLinks = [ a['href'] for a in soup.select("a[href]")]
        return unfilteredLinks
    def regexSearch(self,content,regex):
        return re.search(regex,content)
    def getContent(self,content,cssSelector,attr):
        if content is None or cssSelector is None:
            return []
        soup = BeautifulSoup(content,features="html.parser")
        resultSet = soup.select(cssSelector)
        if attr is not None:
            try:
                return {element[attr] for element in resultSet}
            except Exception:
                pass
        else:
            return set(resultSet)
