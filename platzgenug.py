# -*- coding: utf-8 -*-
## settings
postHourMin = 9 # no posting if hour smaller
postHourMax = 21  # no more posting if hour greater
parkingURL="https://web1.karlsruhe.de/service/Parken/"
parkplatzFlaeche = 12.5 # m2 (analog @verkehrswatchms)
familienWohnungFlaeche = 110 # m2
dataFile = './data.csv'
vergleichsFlaechen = {'Marktplatz':6000,'Friedrichsplatz':12100,'Botanischer Garten':18200,'Ludwigsplatz':1200,'Gutenbergplatz':5300} # in Google Earth gemessen
statements = ["Wo sind die überdachten Fahrradbügel?",
              "Stehen trotzdem noch Autos am Straßenrand?",
              "Karlsruhe: Roter Teppich für Autos.",
              "Jetzt das städtische Klimaschutzkonzept kommentieren: https://beteiligung.karlsruhe.de/content/bbv/details/90/",
              "Sind trotzdem noch Radwege zugeparkt?",
              "Sind dennoch weiter Autos im Halteverbot abgestellt?",
              "Fahren dennoch weiter Autos auf der Suche nach kostenlosen Parkplätzen durch die Stadt?"]
hashtags = ["#MehrPlatzfürsRad","#VerkehrswendeJetzt","#verkehrswende","#autostadt","#nennmichnichtfahrradstadt"]

## imports
from twitterCred import *   # twitterCred.py resides in the code dir, provides consumer_key, consumer_secret, access_token, access_token_secret
from bs4 import BeautifulSoup
import pandas as pd
from random import choice
from numpy import nan,nansum
from requests import get
from twython import Twython # twitter access
from datetime import datetime

    
## initialize variables
theTime = []
parkingName = []
parkingCapacity = []
parkingOpen = []
parkingFree = []

## what time is it?
now = datetime.now()
current_time = now.strftime("%Y-%m-%d %H:%M:%S")
thisHour = int(now.strftime("%H"))

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
    

# compute total sums and fraction
parkingFreeTotal = nansum(parkingFree)
parkingCapacityTotal = nansum(parkingCapacity)


## write to data file
if False:
    df = pd.DataFrame({'Product Name':products,'Price':prices,'Rating':ratings}) 
    df.to_csv('products.csv', index=False, encoding='utf-8')

    # initialize list of lists 
    data = [['tom', 10], ['nick', 15], ['juli', 14]] 
    fullList = {'Name':parkingName,'Capacity':parkingCapacity,'Open':parkingOpen,'Free':parkingFree}

    # Create the pandas DataFrame 
    #df = pd.DataFrame(fullList, columns = ['Name', 'Age']) 
    #df = pd.DataFrame(fullList, columns = ['Name', 'Capacity','Open','Free'])
    df = pd.DataFrame(fullList)
  
    df.to_csv('my_csv.csv', mode='a', header=False)



def assemble_message(parkingFreeTotal,parkingCapacityTotal,parkplatzFlaeche,vergleichsName,statements,hashtags):
    # imports
    from random import choice
    # computations
    parkingFreeFraction = parkingFreeTotal / parkingCapacityTotal
    # make messages
    messageBody = "Im Zentrum von #Karlsruhe sind jetzt "+str(int(parkingFreeTotal))+" von " + str(int(parkingCapacityTotal))+" verfügbaren Auto-Parkhausplätzen ungenutzt ("+str(int(parkingFreeFraction*100))+"%). Für weitere Autos freigehalten: " + str(int(parkingFreeTotal*parkplatzFlaeche)) + "m2 = "+str(round(parkingFractionComp,1))+"x"+vergleichsName+"." 
    # some choices
    statement = choice(statements)
    hashtag = choice(hashtags)
    # assemble
    theMessage = messageBody + ' ' + statement + " " + hashtag
    # done
    return theMessage
    
    
myCsvRow = current_time + "," + str(parkingFreeTotal) + "," + str(parkingCapacityTotal) + '\n'
with open(dataFile,'a') as fd:
    fd.write(myCsvRow)
    

## convert to message and post
if thisHour >= postHourMin:
    if thisHour <= postHourMax:
        vergleichsName = choice(list(vergleichsFlaechen.keys()))
        vergleichsFlaeche = vergleichsFlaechen[vergleichsName]
        statement = choice(statements)
        hashtag = choice(hashtags)
        parkingFreeFraction = parkingFreeTotal / parkingCapacityTotal
        parkingFractionComp = (parkingFreeTotal * parkplatzFlaeche) / vergleichsFlaeche
        theMessage = "Im Zentrum von #Karlsruhe sind jetzt "+str(int(parkingFreeTotal))+" von " + str(int(parkingCapacityTotal))+" verfügbaren Auto-Parkhausplätzen ungenutzt ("+str(int(parkingFreeFraction*100))+"%). Für weitere Autos freigehalten: " + str(int(parkingFreeTotal*parkplatzFlaeche)) + "m2 = "+str(round(parkingFractionComp,1))+"x"+vergleichsName+". " + statement + " " + hashtag
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


