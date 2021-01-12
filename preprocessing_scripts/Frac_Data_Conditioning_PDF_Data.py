

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt


def frac_data_condition():
       df_total = pd.read_csv('masterDF.csv',index_col=0, encoding = 'latin1')
       
       #Get well license # data for formations
       df_formations = pd.read_csv('Well Licence.csv',index_col=False)
       cols = ['LicenceNumber','ProjectedFormation','TerminatingFormation','ProjectedTotalDepth']
       df_formations = df_formations.loc[:,cols]
       df_formations.rename(columns={'ProjectedFormation':'Projected Formation',
                     'TerminatingFormation':'Terminating Formation',
                     'ProjectedTotalDepth':'Projected Total Depth'}, inplace=True)
       #astype() returns a copy so don't need .loc
       df_formations['LicenceNumber'] = df_formations['LicenceNumber'].astype(str)
       df_formations['LicenceNumber'] = df_formations['LicenceNumber'].str.lstrip('0')
       df_formations.to_csv('df_formations.csv')


       #replace all colons in column names.....
       df_total = df_total.rename(columns = lambda x : str(x).replace(":",""))  

       #Format well licence number to string to join
       #astype() returns a copy so don't need .loc
       df_total['Well Licence Number'] = df_total['Well Licence Number'].astype(str)

       print('df_total'+ str(df_total['Well Licence Number'].dtype))
       print('df_formation' + str(df_formations['LicenceNumber'].dtype))

       #rename columns to match app from native PDF column names
       df_total.rename(columns={'Unique Well Identifier':'UWI',
                            'Trade Name':'Component Trade Name',
                            'Licensee Name':'Licensee',
                            'Supplier':'Component Supplier Name',
                            'Purpose':'Additive Purpose',
                            'Ingredient/Family Name':'Ingredient Name',
                            'CAS # / HMIRC #':'CAS # HMIRC #',
                            'Concentration in Component':'Concentration Component',
                            'Concentration in HFF':'Concentration HFF',
                            'Total Water Volume (m3)':'Total Water Volume',
                            'True Vertical Depth (TVD)':'Max True Vertical Depth'}, inplace=True)
       df_total.rename(columns={'Trade Name':'Component Trade Name'}, inplace=True)

       #Change column types for numeric, remove odd characters. If not numeric, fill with NA to be droppped in later step
       df_total['Total Water Volume'] = df_total['Total Water Volume'].astype('str') #Cast to string to replace commas ....
       df_total['Total Water Volume'] =pd.to_numeric(df_total['Total Water Volume'].str.replace(",",""),errors='coerce')
       df_total['Concentration HFF'] =pd.to_numeric(df_total['Concentration HFF'].str.replace("%",""),errors='coerce')
       df_total['Concentration Component'] =pd.to_numeric(df_total['Concentration Component'].str.replace("%",""),errors='coerce')
       #Drop rows with errors
       #df_total = df_total.dropna()

       df = df_total.copy() 
       #Drop columns not needed for unique UWI plottings

       #Keep columns only import per well
       df = df[['UWI', 'Last Fracture Date',
              'Last Submission Date', 'Province', 'AER Field Centre',
              'Surface location', 'Well Licence Number', 'Licensee',
              'Well Name', 'Number of Stages', 'Bottom Hole Latitude',
              'Bottom Hole Longitude', 'Lat/Long Projection',
              'Production Fluid Type', 'Max True Vertical Depth',
              'Total Water Volume', 'Start Date', 'End Date']]



       # df.drop(['Total Water Volume', 'Component Type',
       #        'Component Trade Name', 'Component Supplier Name', 'Additive Purpose',
       #        'Ingredient Name', 'CAS # HMIRC #', 'Concentration Component ',
       #        'Concentration HFF'],axis=1, inplace=True)
       df.drop_duplicates(inplace=True)
       df_total.drop_duplicates(inplace=True)

       #Reset Index
       df['Last Fracture Date'] = pd.to_datetime(df['Last Fracture Date'])
       df['year_month'] = df['Last Fracture Date'].dt.strftime('%Y-%m')
       df['year'] = df['Last Fracture Date'].dt.year
       df['Start Date'] = pd.to_datetime(df['Start Date'])
       df['End Date'] = pd.to_datetime(df['End Date'])

       #Add helper date columns
       df['Days Diff'] = (df['End Date'] - df['Start Date'])/np.timedelta64(1, 'D')
       df['Stages Per Day'] = df['Number of Stages']/(df['Days Diff']+1)#ADD ONE DAY TO FIX SAME DAY FRACS

       #Calculate total water volume per well
       df_water_vol = df_total[['UWI','Total Water Volume','Concentration HFF']][
                                   (df_total['Total Water Volume'] != 0) & 
                                   ((df_total['Ingredient Name'].str.contains('water',case=False)) | 
                                   (df_total['Ingredient Name'].str.contains('No specific ingredients',case=False)))].drop_duplicates()
       df_water_vol = df_water_vol.groupby(by=['UWI','Total Water Volume']).agg('sum')
       df_water_vol = df_water_vol.reset_index()
       df_water_vol['Total Frac Mass'] = df_water_vol['Total Water Volume']/ (df_water_vol['Concentration HFF']/100)
       df_water_vol['Total Frac Mass']  =  df_water_vol['Total Frac Mass'] .round(1) #remove rest of decimals....
       df_water_vol.drop('Concentration HFF',axis=1,inplace=True)

       #Calculate total proppant per well by %
       df_proppant = df_total[df_total['Component Type'] == 'PROPPANT'][['UWI','Concentration HFF']].groupby(by='UWI').agg('sum')
       df_proppant = df_proppant['Concentration HFF'].reset_index()

       #merge columns by UWI column onto original
       df = df.merge(df_proppant,how='left')
       df = df.merge(df_water_vol,how='left')

       #Rename column, calculate metric tonnes proppant placed 1000 m3 = 1000 kg = 1 tonne * Total Proppant %
       df.rename(columns={'Concentration HFF':'Total Proppant %'}, inplace=True)
       df['Total Proppant (tonnes)/Stage'] = ((df['Total Frac Mass'])*(df['Total Proppant %']/100))/df['Number of Stages']
       df['Total Proppant (tonnes)/Stage'] =df['Total Proppant (tonnes)/Stage'].round(1)

       #Join on formation data from Well License File
       df = df.merge(df_formations, how='left',left_on='Well Licence Number', right_on='LicenceNumber')

       #Remove duplicates in case of multiple scrapes of wells
       df.drop_duplicates(inplace=True)
       df_total.drop_duplicates(inplace=True)


       df.to_csv('df_by_well.csv')
       df_total.to_csv('df_total.csv')

