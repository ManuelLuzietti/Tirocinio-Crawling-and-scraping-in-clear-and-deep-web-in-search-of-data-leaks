# -*- coding: utf-8 -*-
"""
Created on Sun Apr 24 14:45:10 2022

@author: manue
"""

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
options = webdriver.ChromeOptions()
options.add_argument("headless") #disable the browser gui display
driver = webdriver.Chrome(options=options,service=Service(ChromeDriverManager().install()))
driver.get("https://www.w3schools.com/html/default.asp")
content = driver.page_source
soup = BeautifulSoup(content,features="html.parser") #parsing
elements = []
for a in soup.select("div.w3-example > h3"):
    elements.append(a)
driver.close()
print(elements)



