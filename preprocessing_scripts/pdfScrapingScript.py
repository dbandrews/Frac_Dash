
# coding: utf-8
import os
from subprocess import call
import io
import numpy as np
import matplotlib.pyplot as plt
from matplotlib import cm
from tabula import read_pdf
import xml.etree.ElementTree as ET
import pandas as pd



#**************************HELPER FUNCTIONS**********************************************************************************
def drop_footer(df, footer_text):
    df_temp=df.copy()
    
    combined_string=''.join(df_temp['text_value'].values.tolist())
    footer_index=str.find(combined_string, footer_text)
    #print(combined_string[footer_index-10:footer_index+10])
    footer_y1=df_temp['y1'].iloc[footer_index]
    footer_y2 =df_temp['y2'].iloc[footer_index]
    print(footer_y1)
    print(footer_y2)
    df_temp=df_temp[df_temp['y1']>footer_y1]
    return df_temp


# In[13]:


def drop_header(df, header_text):
    page = 1
    search_index=0
    df_temp=df.copy()
    combined_string=''.join(df_temp['text_value'].values.tolist())
    while page > 0:
        #print(df_temp.shape[0])
        if df_temp[df_temp['page'] == page].shape[0] > 0:
            header_index = combined_string.find(header_text, search_index)+4
            search_index = header_index + 1
            header_y1 = df['y1'].iloc[header_index]
            df_temp = df_temp[(df_temp['y1']<header_y1) | (df_temp['page'] != page)]
            #pdf_to_plot(df_temp)
            page += 1
        else:
            page = 0
    return df_temp


# In[14]:


def left_bound(df, search_text):
    df_temp = df.copy()
    combined_string = ''.join(df_temp['text_value'].values.tolist())
    search_index = combined_string.find(search_text)
    search_x1 = []
    if search_index == -1:
        search_x1.append(0)
    else:
        search_x1.append(df['x1'].iloc[search_index])
    return search_x1


# In[15]:


def top_bounds(df, search_text):
    df_temp = df.copy()
    combined_string = ''.join(df_temp['text_value'].values.tolist())
    search_index = -1
    counter = 0
    bounds =[]
    while (combined_string.find(search_text, search_index+1) >= 0):
        search_index = combined_string.find(search_text, search_index+1)
        bounds.append(df['y1'].iloc[search_index])
        counter += 1
    return bounds


# In[16]:


def extract_column(df, left, right):
    df_temp = df.copy()
    df_temp = df_temp[(df_temp['x1'] >= left) & (df_temp['x1'] < right)]
    return df_temp
    #**************************HELPER FUNCTIONS**********************************************************************************


def main(filename):


    #call(["python.exe", "C:\ProgramData\Anaconda3\Scripts\pdf2txt.py", "-o", "C:\\Users\\amath\\AnacondaProjects\\output.xml", "C:\\Users\\amath\\AnacondaProjects\\TestTestTest.pdf"])
    #FOR ANDREWS COMPUTER>>>>>>>>
    #call(["python.exe", "C:\ProgramData\Anaconda3\Scripts\pdf2txt.py", "-o", filename[:-3]+"xml", filename])
    #FOR DUSTINS COMPUTER>>>>>>>>>>
    #call(["python.exe", "C:\\Users\Dustin\\Anaconda3\\Scripts\pdf2txt.py", "-o", filename[:-3]+"xml", filename])
    #FOR SUPER COMPUTER>>>>>>>>>>
    call(["python.exe", "C:\\Users\\oakri\\Anaconda3\\Scripts\\pdf2txt.py", "-o", filename[:-3]+"xml", filename])

    #Adjust the default plot size
    fig_size = plt.rcParams["figure.figsize"]
    fig_size[0] = 30
    fig_size[1] = 18
    plt.rcParams["figure.figsize"] = fig_size


    # In[3]:


    #Read header table
    #Transpose for joining later
    df_header =read_pdf(filename, area = [70,50,280,430], guess = False, pandas_options={'header':None})
    df_header = df_header.transpose()
    df_header.columns = df_header.iloc[0,:]
    df_header = df_header.reindex(df_header.index.drop(0))
    df_header = df_header.astype('str',copy=True)


    # In[4]:


    #df_header.info()


    # In[5]:



    tree = ET.parse(filename[:-3]+"xml")
    root = tree.getroot()


    # In[6]:


    dfcols = ['attributes', 'text_value','page']
    df_xml = pd.DataFrame(columns=dfcols)
    page = 1

    while page <= len(tree.findall('page')):
        for text in root[page-1].iter('text'):
            attributes = text.attrib
            text_value = text.text
            df_xml = df_xml.append(
                pd.Series([attributes, text_value, page], index=dfcols),
                ignore_index=True)
        page += 1
        
    #df_xml.info()


    # In[7]:


    df_clean = df_xml.drop(df_xml[df_xml['text_value']=='\n'].index)
    df_clean['attributes'] = df_clean['attributes'].astype('str')
    df_clean['bbox']= df_clean['attributes'].str.split('bbox', expand=True)[1].str.split('size', expand=True)[0]
    df_clean['bbox'] = df_clean['bbox'].str[4:]
    df_clean['bbox'] = df_clean['bbox'].str[:-4]
    df_clean[['x1','y1','x2','y2']] = df_clean['bbox'].str.split(',',expand=True)
    df_clean[['x1','y1','x2','y2']] = df_clean[['x1','y1','x2','y2']].astype('float')
    df_clean = df_clean.dropna()
    #df_clean[df_clean['x1'].isna() != False]


    # In[8]:

    
    def pdf_to_plot(df):
        """pdf_to_plot requires a dataframe with columns: page, x1, y1, and text_value"""
        fig, ax = plt.subplots()
        df_plot = df.copy()
        df_plot['y1']=df_plot['y1'].values-(df_plot['page']-1)*565.506
        df_plot['y2']=df_plot['y2'].values-(df_plot['page']-1)*565.506
        df_plot['y1'] = (df_plot['y1']+df_plot['y2'])/2
        df_plot['x1'] = (df_plot['x1']+df_plot['x2'])/2
        ax.scatter(df_plot['x1'].values,df_plot['y1'].values, s=0.01, c=df_plot['x1'].values, cmap=cm.plasma)
        for i, txt in enumerate(df_plot['text_value'].values):
            ax.annotate(txt, (df_plot['x1'].iloc[i],df_plot['y1'].iloc[i]),fontsize=5)


    # In[9]:


    #pdf_to_plot(df_clean)


    # In[10]:

    #pdf_to_plot(df_clean)
    #plt.show()
    df_clean['text_value'][df_clean['text_value'].str.startswith('(cid')]= ' '
    df_clean = drop_footer(df_clean, 'Page: ')

    
   
    combined_string=''.join(df_clean['text_value'].values.tolist())
    print(df_clean['text_value'].size)
    combined_string_encoded = combined_string.encode(encoding='UTF-8',errors='ignore')#String together characters, verify encoding
    combined_string = combined_string_encoded.decode()
    comment_index=str.find(combined_string, 'Comments')
    print(comment_index)
    comment_y1=df_clean['y1'].iloc[comment_index]
    print(comment_y1)
    comment_page=df_clean['page'].iloc[comment_index]
    df_trim=df_clean[(df_clean['page'] != comment_page) | (df_clean['y1']>comment_y1)]


    # In[11]:


    index=0
    start_end_index=[]
    while index < len(combined_string):
            index = combined_string.find('Start/End', index)
            if index == -1:
                index = len(combined_string)
            else:
                start_end_index = np.append(start_end_index, index)
            index += 1
    start_end_index=start_end_index.astype('int')
    start_end1_y1=df_clean['y1'].iloc[start_end_index[0]]
    start_end1_page=df_clean['page'].iloc[start_end_index[0]]
    df_trim=df_trim[(df_trim['page'] != start_end1_page) | (df_trim['y1']<=start_end1_y1)]
    

    # In[12]:

    # In[17]:

        #pdf_to_plot(df_trim)
    df_body = drop_header(df_trim, 'HFF(% by mass)')
    #pdf_to_plot(df_body)

    
    # In[18]:


    df_body['y1']=df_body['y1']+(df_body['page']*612)-612


    # In[19]:


    df_body['y2']=df_body['y2']+(df_body['page']*612)-612


    # In[20]:


    cell_x1s = left_bound(df_clean, 'Fracture Start/End Date:')
    cell_x1s.extend(left_bound(df_clean, 'Component Type'))
    cell_x1s.extend(left_bound(df_clean, 'Trade Name'))
    cell_x1s.extend(left_bound(df_clean, 'Supplier'))
    cell_x1s.extend(left_bound(df_clean, 'Purpose'))
    cell_x1s.extend(left_bound(df_clean, 'Ingredient/Family Name'))
    cell_x1s.extend(left_bound(df_clean, 'CAS # / HMIRC #'))
    cell_x1s.extend(left_bound(df_clean, 'Concentration in Component'))
    cell_x1s.extend(left_bound(df_clean, 'Concentration in HFF'))
    cell_x1s.extend([72*11])
    cell_x1s = sorted(cell_x1s)
    labels = range(0,9)
    df_body['Column'] = pd.cut(df_body['x1'],cell_x1s,labels=range(0,9), right=False)
    df_body['Column'] = df_body['Column'].astype('int64')

    
    # In[21]:


    #NEED TO FACTOR IN PAGE NUMBERS! ORDERS ROWS FROM BOTTOM UP!
    cell_y1s = top_bounds(df_body,"CARRIER FLUID")
    cell_y1s.extend(top_bounds(df_body,"PROPPANT"))
    cell_y1s.extend(top_bounds(df_body,"ADDITIVE"))
    cell_y1s.extend([0])
    #THIS WILL NOT WORK ONCE PAGE NUMBERS ARE FACTORED IN
    cell_y1s.extend([612*np.max(df_body['page'])])
    cell_y1s = sorted(cell_y1s)
    df_body['Row'] = pd.cut(df_body['y1'], cell_y1s, labels=False)
    #df_body
    #(cell_y1s)


    # In[22]:


    #Build the columns to put the components in
    column_names = ['Fracture Start/End Date:','Component Type','Trade Name', 'Supplier', 'Purpose', 
    'Ingredient/Family Name', 'CAS # / HMIRC #', 'Concentration in Component','Concentration in HFF']
    useful = pd.DataFrame(index=df_body['Row'].unique(), columns=column_names)
    row_min = np.min(df_body['Row'].values)
    row_max = np.max(df_body['Row'].values)
    column_min = np.min(df_body['Column'].values)
    column_max = np.max(df_body['Column'].values)
    row_min
    row_max
    column_min
    column_max

    #df_body[df_body.isna().any(axis=1)]
    #df_body


    # In[23]:


    #Build each cells values
    row = row_min
    while row <= row_max:
        column = column_min
        while column <= column_max:
            cell_value = ''.join(df_body['text_value'][(df_body['Row']==row) & (df_body['Column']==column)].values.tolist())
            useful.iloc[row,column] = cell_value
            column += 1
        row += 1


    # In[24]:


    #Append header table to all rows of components
    useful.sort_index(axis=0, inplace = True)
    useful['Unique Well Identifier:'] = df_header['Unique Well Identifier:'][1]
    useful = useful.join(df_header.set_index('Unique Well Identifier:'),on='Unique Well Identifier:')


    # In[34]:


    #Create Start/End Date columns
    useful = useful.sort_values(by='Fracture Start/End Date:', ascending=False)
    useful = useful.reset_index(drop=True)
    useful['Start Date:'] = np.nan
    useful['End Date:'] = np.nan
    useful[['Start Date:','End Date:']] = useful['Fracture Start/End Date:'][0].split('-')
    #useful.info()

    return useful
