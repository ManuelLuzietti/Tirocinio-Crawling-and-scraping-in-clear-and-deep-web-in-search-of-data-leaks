import scrapy


class LinksSpider(scrapy.Spider):
    name = "links"

    def start_requests(self):
        urls = ["https://www.w3schools.com/",
                "https://www.w3schools.com/tags/default.asp"]
        for url in urls:
            yield scrapy.Request(url, callback=self.parse)
    
    def parse(self, response):
        for numm,link in enumerate(response.css("a"),start=1):
            yield {numm:link.get(),
                    "link": link.css("a").get()}

