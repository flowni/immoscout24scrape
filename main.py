import bs4 as bs
from bs4 import BeautifulSoup
import urllib.request
import time
from datetime import datetime
import pandas as pd
import json
from selenium import webdriver
from selenium.webdriver import DesiredCapabilities

import xlsxwriter



# %% pd to save data

df = pd.DataFrame()


# %% go to immoscout page

opt = webdriver.FirefoxOptions()
opt.add_argument('user-agent="Mozilla/5.0 (Windows NT 10.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.141 Safari/537.36"')

driver = webdriver.Firefox(firefox_options=opt)



#make right header of firefox

def go_to_page(pagenumber):
    link = "https://www.immobilienscout24.de/Suche/de/bayern/muenchen-kreis/wohnung-mieten?sorting=2&pagenumber=" + str(pagenumber)
    driver.get(link)




# %% get content of page (title, , Ort, miete, sqm, Anzahl Zimmer, sonstige Tiles, Wer inseriert?, Link!!!


# get content of one tile
def get_information_of_ad(adnumber):
    #get html code
    html = driver.page_source
    soup = BeautifulSoup(html)
    all_flats_on_page = soup.find_all('article')

    #could implement scroll to view so we get the data of the things we are looking at, would be pretty cool

    #get the data of the ads
    title = all_flats_on_page[adnumber].find_all('h5')[0].text.replace('NEU', '')
    location = all_flats_on_page[adnumber].select('.result-list-entry__address')[0].text
    kaltmiete = all_flats_on_page[adnumber].find_all('dd')[0].text
    wohnflaeche = all_flats_on_page[adnumber].find_all('dd')[1].text
    count_zimmer = all_flats_on_page[adnumber].find_all('dd')[2].select('.onlyLarge')[0].text
    tiles = all_flats_on_page[adnumber].find_all('li')
    extras = ""
    for tile in tiles:
        extras += tile.text + ", "
    extras = extras[:-2]
    makler = all_flats_on_page[adnumber].select('.result-list-entry__realtor-data-container')[0].text
    link = all_flats_on_page[adnumber].select('a.result-list-entry__brand-title-container')[0].get('href')

    #save data in dict
    d = dict()
    d['title'] = title
    d['location'] = location
    d['kaltmiete'] = kaltmiete
    d['wohnflaeche'] = wohnflaeche
    d['count_zimmer'] = count_zimmer
    d['extras'] = extras
    d['makler'] = makler
    d['link'] = link

    return d




def get_all_ads_on_page():
    #get content of all inserate and save in Dataframe
    global df
    html = driver.page_source
    soup = BeautifulSoup(html)
    all_flats_on_page = soup.find_all('article')
    for i in range(len(all_flats_on_page)):
        data_of_ad_dict = get_information_of_ad(i)
        # only add if ad is not already in it -> if find one then stop, because list is sorted
        if not df.empty and data_of_ad_dict['title'] in df['title'].values:
            print("Already in df: " + data_of_ad_dict['title'])
            break
        df = df.append(data_of_ad_dict, ignore_index=True)
        print("Added: " + data_of_ad_dict['title'])




# %% go through all pages
#https://www.immobilienscout24.de/Suche/de/bayern/muenchen-kreis/wohnung-mieten?sorting=2&pagenumber=1

#get number of pages by dropdown, or just have a quick look -> 13 pages
for x in range(2, 14):
    go_to_page(x)
    get_all_ads_on_page()
    time.sleep(46)



# %% clean and modify data

df['kaltmiete_raw'] = df['kaltmiete'].str.replace(" €", "")
df['wohnflaeche_wohnflaeche_raw'] = df['wohnflaeche'].str.replace(" m²", "")







# %% clean and modify data

df['kaltmiete_raw'] = df['kaltmiete_raw'].str.replace(".","")
df['wohnflaeche_wohnflaeche_raw'] = df['wohnflaeche_wohnflaeche_raw'].str.replace(".","")

df['kaltmiete_raw'] = df['kaltmiete_raw'].str.replace(",",".")
df['wohnflaeche_wohnflaeche_raw'] = df['wohnflaeche_wohnflaeche_raw'].str.replace(",",".")

# %% clean and modify data



df['kaltmiete_raw'] = df['kaltmiete_raw'].astype('float')
df['wohnflaeche_wohnflaeche_raw'] = df['wohnflaeche_wohnflaeche_raw'].astype('float')

df['preis/sqm'] = df['kaltmiete_raw'] / df['wohnflaeche_wohnflaeche_raw']



# %% save to xlsx

# Create a Pandas Excel writer using XlsxWriter as the engine.
writer = pd.ExcelWriter('inserate.xlsx', engine='xlsxwriter')
# Convert the dataframe to an XlsxWriter Excel object.
df.to_excel(writer, sheet_name='Sheet1')
# Close the Pandas Excel writer and output the Excel file.
writer.save()



