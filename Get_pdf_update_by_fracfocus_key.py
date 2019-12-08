from bs4 import BeautifulSoup, SoupStrainer
import requests
import re
import selenium
from selenium import webdriver
import time
import os, os.path

def Get_pdf_update_by_fracfocus_key(fracfocus_nums,path_to_driver):
    '''Will go to FracFocus.ca and scrape pdfs for Alberta wells by 7 digit license number. 
    Checks sub folder from Script "AB_PDFs" for if the pdf to get alread exists.
    options: list of license numbers (7 digit numbers), absolute path to web driver including executable name
    Copies PDF's to Folder AB_PDFs where script is run from
    ***Requires selenium
    '''
    options_in = webdriver.ChromeOptions()
    download_folder = os.path.abspath(os.path.join("AB_PDFs"))
    if os.path.isdir(download_folder) != True:
        os.makedirs(download_folder)
    
    #Check what already exists in the folder
    pdf_list = []
    for (dirpath, dirnames, filenames) in os.walk(download_folder):
        pdf_list.extend(filenames)
        break
    
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
    for frac_num in fracfocus_nums:
        if str(frac_num)+'.pdf' in set(pdf_list):
            True
        else:
                driver.get('http://fracfocus.ca/find_well/download/AB/'+str(frac_num));
        
    driver.close()

    #Delete out all Frac PDFS with no actual data
    fileiter = (os.path.join(root, f)
    for root, _, files in os.walk(download_folder)
    for f in files)
    smallfileiter = (f for f in fileiter if os.path.getsize(f) < 131 * 1024)# File size in KiloBytes *1024
    for small in smallfileiter:
        os.remove(small)
