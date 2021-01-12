import pandas as pd
import numpy as numpy
from Get_pdf_by_fracfocus_key import Get_pdf_by_fracfocus_key


#### Note: If Frac Focus times out this script will break.....
data = pd.read_fwf('https://www.aer.ca/data/conwell/ConWell.txt', colspecs=[(0,19),(21,30),(31,66),(67,84),(86,103),(105,123)], header=17)
#data.columns = ["UWI", "License Number", "Licensee", "Confidential type","Conf. Below","Confidential Release Date"]
data = data.drop(data.index[0])
data_conf = data[data['Conf. Release Date'] != 'no date avail']
license_num_list = data_conf['Licence #'].values
data_conf.loc[:,'Frac Focus Key'] = (data_conf['Well Location'].str.slice(9,12) + 
                               data_conf['Well Location'].str.slice(16,17) + 
                               data_conf['Well Location'].str.slice(13,15) +
                               data_conf['Well Location'].str.slice(6,8)+
                               data_conf['Well Location'].str.slice(3,5)+
                              data_conf['Well Location'].str.slice(0,2)+
                              data_conf['Well Location'].str.slice(18,19))
frac_key_list = data_conf['Frac Focus Key'].values

Get_pdf_by_fracfocus_key(frac_key_list,r'C:/Program Files (x86)/chromedriver_win32/chromedriver.exe')