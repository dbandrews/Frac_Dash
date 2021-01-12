from bs4 import BeautifulSoup, SoupStrainer
import requests
import re
import selenium
from selenium import webdriver
import time
import os

def Get_pdf_by_license(license_nums,path_to_driver):
    '''Will go to FracFocus.ca and scrape pdfs for Alberta wells by 7 digit license number. 
    If license not found will print license numbers that didn't match to command line.
    options: list of license numbers (7 digit numbers), absolute path to web driver including executable name
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
    time.sleep(2)
    # Start looping through license numbers and downloading
    for license_num in license_nums:

        search_box = driver.find_element_by_name('op')
        license_box = driver.find_element_by_xpath('//*[@id="edit-licence-num"]')
        license_box.clear()
        license_box.send_keys(license_num)
        search_box.submit()
        time.sleep(1)

        result_check = driver.find_element_by_xpath('//*[@id="fracResults"]/table[2]/tbody/tr/td[1]')
        if result_check.text == 'No wells matching the selected query criteria have hydraulic fracturing fluid data available':
            print('No match found for license #:'+str(license_num))
        else:
            pdf_button = driver.find_element_by_xpath('//*[@id="fracResults"]/table[2]/tbody/tr[1]/td[1]/a')
            pdf_button.click()
            time.sleep(5)
        #Get the first record returned if one is returned

    driver.close()
