# -*- coding: utf-8 -*-
## settings
doSaveData = True
doTweet = True
postHourMin = 9 # no posting if hour smaller
postHourMax = 21  # no more posting if hour greater
parkingURL="https://web1.karlsruhe.de/service/Parken/"
parkplatzFlaeche = 12.5 # m2 (analog @verkehrswatchms)
minParkingReportFractionForValid = 0.5  # minimum fraction of parking garages with valid reports needed
familyAppArea = 110 # m2
dataFileBase = 'data.csv'
vergleichsFlaechen = {'Marktplatz':6000,'Friedrichsplatz':12100,'Botanischer Garten':18200,'Ludwigsplatz':1200,'Gutenbergplatz':5300,'Schlossgartenspielplatz':5100} # in Google Earth gemessen
alternativeUseAreas = {'Bäume': parkplatzFlaeche/1.1, 'Cafétische oder Ruhebänke':parkplatzFlaeche/1.5, 'Kinderwippen':parkplatzFlaeche/.9 ,'Fahrradbügelstellplätze':parkplatzFlaeche/9.}  # aus Parking Day-Fotos geschaetzt
statements = ["Wo sind die überdachten Fahrradbügel?",
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
from numpy import nan,nansum,where,isnan
from requests import get
from twython import Twython # twitter access
from datetime import datetime
from os import getcwd

## initialize variables
theTime = []
parkingName = []
parkingCapacity = []
parkingOpen = []
parkingFree = []
dataDir = getcwd()
dataFile = dataDir + '/' + dataFileBase


## what time is it?
now = datetime.now()
current_time = now.strftime("%Y-%m-%d %H:%M:%S")
thisHour = int(now.strftime("%H"))

## get info from web page
response = get(parkingURL)
content = response.text
soup = BeautifulSoup(content,'lxml')

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
parkingCapacityTotal = nansum(parkingCapacity)
if (nansum(where(isnan(parkingFree),0,1))/float(len(parkingFree))) >= minParkingReportFractionForValid:
    parkingFreeTotal = nansum(parkingFree)
    option = -1  # choose message at random
else:
    parkingFreeTotal = nan
    option = 3  # print message 3

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

if doSaveData:
    myCsvRow = current_time + "," + str(parkingFreeTotal) + "," + str(parkingCapacityTotal) + '\n'
    with open(dataFile,'a') as fd:
        fd.write(myCsvRow)
    


def assemble_message(parkingFreeTotal,parkingCapacityTotal,parkplatzFlaeche,vergleichsFlaechen,familyAppArea,alternativeUseAreas,statements,hashtags,option):
    # imports
    from random import choice

    # computations
    parkingFreeFraction = parkingFreeTotal / parkingCapacityTotal
    parkingFreeArea = parkingFreeTotal*parkplatzFlaeche

    # select area to compare to (should be smaller than free parking space)
    vergleichsFlaeche = 10000000
    iterMax = 20
    i = 0
    while vergleichsFlaeche >= parkingFreeArea:
        i+=1
        vergleichsName = choice(list(vergleichsFlaechen.keys()))
        vergleichsFlaeche = vergleichsFlaechen[vergleichsName]
        if i >= iterMax:
            break

    # compute fraction of area
    parkingFractionComp = (parkingFreeTotal * parkplatzFlaeche) / vergleichsFlaeche
        
    # make messages (choose one)
    if option < 0:
        option = choice([1,2,3])
    
    ## fraction, comparison to popular space
    if option == 1:
        messageBody = "Im Zentrum von #Karlsruhe sind jetzt "+str(int(parkingFreeTotal))+" von " + str(int(parkingCapacityTotal))+" Auto-Parkhausplätzen ungenutzt ("+str(int(parkingFreeFraction*100))+"%). Für weitere Autos freigehalten: " + str(int(parkingFreeTotal*parkplatzFlaeche)) + "m2 = "+str(round(parkingFractionComp,1)).replace('.',',')+" mal "+vergleichsName+"."
        statement = choice(statements)
        hashtag = choice(hashtags)

    ## free area, comparison to alternative use
    elif option == 2:
        alternativeUseString = ''
        eachUseArea = parkingFreeArea / len(alternativeUseAreas)
        i = 0
        for x in alternativeUseAreas:
            thisUseNumber = eachUseArea / alternativeUseAreas[x]
            alternativeUseString += str(int(thisUseNumber)) + ' ' + x
            if i == len(alternativeUseAreas)-2:
                alternativeUseString += ' und '
            if i < len(alternativeUseAreas)-2:
                alternativeUseString += ', '
            i +=1
        
        messageBody = "#Karlsruhe Zentrum: "+str(int(parkingFreeTotal))+ " von "+ str(int(parkingCapacityTotal)) +" Parkhausplätzen ungenutzt. Wenn entsprechend Autos von den Straßenrändern verschwänden, würden " + str(int(parkingFreeTotal*parkplatzFlaeche)) +"m2 frei, z.B. für " + alternativeUseString + "."
        statement = choice(['',''])
        hashtag = choice(['#StaedteFuerMenschen','#Verkehrswende','#Autostadt'])

    ## total area, climate goals, average CO2 and PM10 loading
#    messageBody = "Die Stadt #Karlsruhe will bis 2030 58% ihrer CO2-Emissionen gegenüber 2010 einsparen. "
#    messageBodies.append(messageBodyTemp)
#    statement = choice([''])
#    hashtag = choice(['#','#'])

    
    ## total area, comparison to appartments
    elif option == 3:
        messageBody = "In #Karlsruhe locken jetzt "+str(int(parkingCapacityTotal))+" Parkhausplätze Autos ins Herz der Stadt, gesamt: " + str(int(parkingCapacityTotal*parkplatzFlaeche))+"m2. Daraus könnte man " + str(int(parkingCapacityTotal*parkplatzFlaeche/familyAppArea)) + " Familienwohnungen mit je 110m2 machen."
        statement = choice(['Prioritäten...'])
        hashtag = choice(['#StaedteFuerMenschen','#Wohnungsnot','#Autostadt'])
    
    # assemble
    theMessage = messageBody + ' ' + statement + " " + hashtag

    # done
    return theMessage
    
    

## convert to message and post
if thisHour >= postHourMin:
    if thisHour <= postHourMax:
        theMessage = assemble_message(parkingFreeTotal,parkingCapacityTotal,parkplatzFlaeche,vergleichsFlaechen,familyAppArea,alternativeUseAreas,statements,hashtags,option)
        
#        import code;code.interact(local=locals())


        # "x von y (z%) von Gesamtkapazitaet frei"
        # "x von y (z%) von aktueller Kapazitaet frei"
        # max letzte 24 h, min, mean


        ## post to twitter
        if doTweet:
            twitter = Twython(
                consumer_key,
                consumer_secret,
                access_token,
                access_token_secret
            )
            twitter.update_status(status=theMessage)
            #print("Tweeted: %s" % theMessage)
        else:
            print(theMessage,len(theMessage))

