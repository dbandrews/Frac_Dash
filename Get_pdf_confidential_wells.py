import pandas as pd
import numpy as numpy
from Get_pdf_by_license import Get_pdf_by_license


#### Note: If Frac Focus times out this script will break.....
data = pd.read_fwf('https://www.aer.ca/data/conwell/ConWell.txt', colspecs=[(0,19),(21,30),(31,66),(67,84),(86,103),(105,123)], header=17)
#data.columns = ["UWI", "License Number", "Licensee", "Confidential type","Conf. Below","Confidential Release Date"]
data = data.drop(data.index[0])
data_conf = data[data['Conf. Release Date'] != 'no date avail']
license_num_list = data_conf['Licence #'].values

Get_pdf_by_license(license_num_list,r'C:/Program Files (x86)/chromedriver_win32/chromedriver.exe')