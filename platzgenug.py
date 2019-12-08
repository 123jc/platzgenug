# -*- coding: utf-8 -*-
## settings
parkingURL="https://web1.karlsruhe.de/service/Parken/"
parkplatzFlaeche = 12.5 # m2 (analog @verkehrswatchms)
vergleichsFlaechen = {'Marktplatz':6000,'Friedrichsplatz':12100,'Botanischer Garten':18200,'Ludwigsplatz':1200,'Gutenbergplatz':5300} # in Google Earth gemessen


## imports
from twitterCred import *   # twitterCred.py resides in the code dir, provides consumer_key, consumer_secret, access_token, access_token_secret
from bs4 import BeautifulSoup
import pandas as pd
from random import choice
from numpy import nan,nansum
from requests import get
from twython import Twython # twitter access

    
## initialize variables
theTime = []
parkingName = []
parkingCapacity = []
parkingOpen = []
parkingFree = []

## get info from web page
response = get(parkingURL)
content = response.text
soup = BeautifulSoup(content)

parking_containers = soup.find_all('div', class_ = 'parkhaus')

for i in list(range(len(parking_containers))):
    thisParkingName = parking_containers[i].a.text
    thisParkingOpen = True
    if len(parking_containers[i].find_all('div', class_ = 'geschlossen')) > 0:
        thisParkingFree = nan   # closed
        thisParkingOpen = False
        thisParkingCapacity = nan
    elif len(parking_containers[i].find_all('div', class_ = 'fuellstand')) < 1:
        thisParkingFree = nan   # no data
    else:
        temp = parking_containers[i].div.text # div: offline, fuellstand
        thisParkingFree = int(temp[:temp.find('\n')])

    if thisParkingOpen:
        temp = parking_containers[i].text
        thisParkingCapacity = int(temp[temp.find('gesamt')+7:temp.find('Parkpl')-1])

    #print(thisParkingName,thisParkingOpen,thisParkingFree,thisParkingCapacity)
    # append to lists
    parkingName.append(thisParkingName)
    parkingCapacity.append(thisParkingCapacity)
    parkingOpen.append(thisParkingOpen)
    parkingFree.append(thisParkingFree)
    
    

## write to data file
if False:
    df = pd.DataFrame({'Product Name':products,'Price':prices,'Rating':ratings}) 
    df.to_csv('products.csv', index=False, encoding='utf-8')



## convert to message

#import code;code.interact(local=locals())

vergleichsName = choice(list(vergleichsFlaechen.keys()))
vergleichsFlaeche = vergleichsFlaechen[vergleichsName]

parkingFreeTotal = nansum(parkingFree)
parkingCapacityTotal = nansum(parkingCapacity)
parkingFreeFraction = parkingFreeTotal / parkingCapacityTotal
parkingFractionComp = (parkingFreeTotal * parkplatzFlaeche) / vergleichsFlaeche
theMessage = "Im Zentrum von #Karlsruhe sind jetzt "+str(int(parkingFreeTotal))+" von " + str(int(parkingCapacityTotal))+" verfügbaren Auto-Parkhausplätzen ungenutzt ("+str(int(parkingFreeFraction*100))+"%). Für weitere Autos freigehalten: " + str(int(parkingFreeTotal*parkplatzFlaeche)) + "m2 = "+str(round(parkingFractionComp,1))+"x"+vergleichsName+". Stehen trotzdem noch Autos am Straßenrand?"
#print(theMessage)

#import code;code.interact(local=locals())


# "x von y (z%) von Gesamtkapazitaet frei"
# "x von y (z%) von aktueller Kapazitaet frei"
# max letzte 24 h, min, mean

## post to twitter
twitter = Twython(
    consumer_key,
    consumer_secret,
    access_token,
    access_token_secret
)
twitter.update_status(status=theMessage)
#print("Tweeted: %s" % theMessage)
