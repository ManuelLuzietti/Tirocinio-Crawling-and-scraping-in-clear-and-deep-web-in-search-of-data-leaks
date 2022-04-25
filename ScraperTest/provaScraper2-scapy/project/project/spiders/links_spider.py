import scrapy


class LinksSpider(scrapy.Spider):
    name = "links"

    def start_requests(self):
        urls = ["http://c32zjeghcp5tj3kb72pltz56piei66drc63vkhn5yixiyk4cmerrjtid.onion/"]
        for url in urls:
            yield scrapy.Request(url, callback=self.parse)
    
    def parse(self, response):
        for numm,link in enumerate(response.css("a"),start=1):
            yield {numm:link.get()}

