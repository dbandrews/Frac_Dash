from bs4 import BeautifulSoup, SoupStrainer
import requests
import re
import selenium
from selenium import webdriver
import time
import os

def Get_pdf_batch(pdf_per_page,num_pages,path_to_driver):
    '''Takes in number of pdfs from top of each page, number of pages of most recent Fracs to scrape pdf's from. 100 pdf's per page on Frac Focus.
    options: num pdfs from top of page (max = 100), number of pages to scrape, absolute path to web driver including executable name
    Copies PDF's to Folder AB_PDFs where script is run from
    ***Requires selenium
    '''

    options_in = webdriver.ChromeOptions()
    download_folder = os.path.abspath(os.path.join("AB_PDFs"))
    if os.path.isdir(download_folder) != True:
        os.makedirs(download_folder)
    
   
    profile = {"plugins.plugins_list": [{"enabled": False,
                                        "name": "Chrome PDF Viewer"}],
            "download.default_directory": download_folder,
            "download.extensions_to_open": ""}
    options_in.add_experimental_option("prefs", profile)
    options_in.add_argument("--disable-extensions")
    options_in.add_argument("--bwsi")
    driver = webdriver.Chrome(executable_path=path_to_driver,options = options_in)
    driver.get('http://fracfocus.ca/find_well/AB');
    time.sleep(1)
    search_box = driver.find_element_by_name('op')
    #search_box.send_keys('ChromeDriver')
    search_box.submit()
    time.sleep(1)
    #Sort by most recent so we download more recent fracs first...
    sort_button = driver.find_element_by_xpath('//*[@id="fracResults"]/table[2]/thead/tr/th[3]/a')
    sort_button.click()
    time.sleep(1)

    #Now on the first landing page for pdf's! time to start looping
    #Set Chrome Options to auto download clicked PDF links and set folder to get them..
    #Check for all PDF clickable links..
    for j in range(1,num_pages+1):
        for i in range(1,pdf_per_page+1):
            pdf_button = driver.find_element_by_xpath('//*[@id="fracResults"]/table[2]/tbody/tr['+str(i)+']/td[1]/a')
            pdf_button.click()
            time.sleep(5)
        if j != num_pages: #only click to next page if not on last one requested
            next_button = driver.find_element_by_xpath('//*[@title="Go to next page"]')
            next_button.click()
            time.sleep(2)

    driver.close()
