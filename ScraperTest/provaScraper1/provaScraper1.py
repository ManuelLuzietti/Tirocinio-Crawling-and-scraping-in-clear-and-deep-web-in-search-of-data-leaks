# -*- coding: utf-8 -*-
"""
Created on Sun Apr 24 14:45:10 2022

@author: manue
"""

def main(URL):
    from selenium import webdriver
    from selenium.webdriver.chrome.service import Service
    from webdriver_manager.chrome import ChromeDriverManager
    from bs4 import BeautifulSoup
    options = webdriver.ChromeOptions()
    options.add_argument("--headless") #disable the browser gui display
    options.add_argument("--proxy-server=socks5://127.0.0.1:9050")
    options.add_argument('user-agent= Mozilla/5.0 (X11; Linux x86_64; rv:91.0) Gecko/20100101 Firefox/91.0')
    driver = webdriver.Chrome(options=options,service=Service(ChromeDriverManager().install()))
    driver.get(URL)
    #print(driver.page_source)
    content = driver.page_source
    soup = BeautifulSoup(content,features="html.parser") #parsing
    elements = []
    for a in soup.select('a[href]'):
        elements.append(a)
    driver.close()
    print(elements)
    

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        exit()
    main(sys.argv[1])
