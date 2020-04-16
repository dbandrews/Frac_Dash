from pdfScrapingScript import main
import os 
import pandas as pd
import shutil
from Get_pdf_update_batch import Get_pdf_update_batch
from Frac_Data_Conditioning_PDF_Data import frac_data_condition
import datetime as dt

cwd = os.getcwd()
downloadedDir = os.path.join(cwd, 'AB_PDFs')
processedDir = os.path.join(cwd, 'Processed')
errorDir = os.path.join(cwd, 'Error')
masterDF = pd.read_csv('masterDF.csv',index_col=0)

Get_pdf_update_batch(100,5, os.path.join(cwd, 'chromedriver.exe'))

for filename in os.listdir(downloadedDir):
    if filename.lower().endswith(".pdf"):
        try:
            testDF = main(os.path.join(downloadedDir,filename))
            masterDF = masterDF.append(testDF,ignore_index=True)
            masterDF.to_csv("masterDF.csv")
            #testDF.to_csv(filename[:-3]+"csv")
            try:
                shutil.move(os.path.join(downloadedDir,filename), processedDir)
            except:
                True
        except:
            print('Error with file: ' + filename)
            try:
                shutil.move(os.path.join(downloadedDir,filename), errorDir)
            except:
                True

#Write out master df                
masterDF.to_csv("masterDF.csv")

#Convert raw parsed csv to usable files for Dash app
frac_data_condition()

#Pull most recent git repo to prod folder
os.chdir(os.path.join(cwd, 'ill-try-spinning','ill-try-spinning Prod'))
os.system("git pull heroku master")
os.chdir(cwd)

#Move to app folder
prod_folder = os.path.join(cwd, 'ill-try-spinning\\ill-try-spinning Prod\\app_folder')
test_folder = os.path.join(cwd, 'ill-try-spinning')

shutil.copy(os.path.join(cwd,'df_total.csv'),prod_folder)
shutil.copy(os.path.join(cwd,'df_total.csv'),test_folder)

shutil.copy(os.path.join(cwd,'df_by_well.csv'),prod_folder)
shutil.copy(os.path.join(cwd,'df_by_well.csv'),test_folder)

#Update heroku
#Time stamp commit to git repo
today = dt.date.today()
today_string = today.strftime('%Y-%m-%d')
os.chdir(os.path.join(cwd, 'ill-try-spinning','ill-try-spinning Prod'))
os.system("git add .")
os.system("git commit -m '"+today_string+"'")
os.system("git push heroku master")




