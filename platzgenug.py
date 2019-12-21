# -*- coding: utf-8 -*-
## settings
doSaveData = True
doTweet = True
postHourMin = 9 # no posting if hour smaller
postHourMax = 21  # no more posting if hour greater
dailyFigHour = 23  # produce and post daily figure at this time
dailyFigMinFreeLimit = 1000 # only post if at least this many spots were free
parkingURL="https://web1.karlsruhe.de/service/Parken/"
parkplatzFlaeche = 12.5 # m2 (analog @verkehrswatchms)
minParkingReportFractionForValid = 0.5  # minimum fraction of parking garages with valid reports needed
familyAppArea = 110 # m2
dataFileBase = 'data.csv'
dailyPlotFileBase = 'daily.png'
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
dailyPlotFile = dataDir + '/' + dailyPlotFileBase

## some functions
def plot_daily(dataFile,dailyPlotFile,endTime=''):
    """Produce a plot of the last 24h"""
    # imports
    import pandas as pd
    import matplotlib.pyplot as plt
    from matplotlib.dates import DateFormatter,HourLocator,DayLocator
    from matplotlib import use
    from numpy import nanmax,nanmin,nanargmin
    from datetime import timedelta
    import seaborn as sns
    use('Agg') # no X
    # read data from file
    df = pd.read_csv(dataFile, parse_dates=[0],names=['datetime','free','capacity'],header=None)
    # select last 24h
    if endTime == '':  # default, nothing specified
        endTime = df['datetime'].iloc[-1]
    startTime = endTime - timedelta(hours=24,minutes=20)
    mask = (df['datetime'] > startTime) & (df['datetime'] <= endTime)
    dfplot = df.loc[mask]
    # extract some numbers
    capacityMax = nanmax(dfplot['capacity'])
    capacityMin = nanmin(dfplot['capacity'])
    freeMax = nanmax(dfplot['free'])
    freeMin = nanmin(dfplot['free'])
    freeMinLoc = nanargmin(dfplot['free'])
    # set labels
    figTitle = 'Karlsruhe wünscht sich noch mehr Autos im Zentrum'
    labelFree = 'Gemeldete$^{*}$ Vakanz (min:' + str(int(freeMin)) + ", max: " + str(int(freeMax)) + ")"
    labelCapacity = 'Gemeldete$^{*}$ Kapazit\"at (min:' + str(int(capacityMin)) + ", max: " + str(int(capacityMax)) + ")"
    labelUsed = "Belegung (rechnerisch)"
    # produce plot
    sns.set()
    fig = plt.figure()
    ax = fig.add_subplot(111)
    x_dates = dfplot['datetime']
    itemFree = ax.plot(x_dates,dfplot['free'],label=labelFree)
    itemCapacity = ax.plot(x_dates,dfplot['capacity'],label=labelCapacity)
    itemFreeFill = ax.fill_between(x_dates,0,dfplot['free'])
    itemUsedFill = ax.fill_between(x_dates,dfplot['free'],dfplot['capacity'],label=labelUsed)
    ax.set_title(figTitle)
    ax.set_ylabel("Parkhausplätze im Zentrum")
    ax.set_xlabel("Zeit")
#    ax.legend([itemCapacity,itemFree],[labelCapacity,labelFree])
    # set text elements
    ax.annotate(str(int(freeMin)), xy=(freeMinLoc, freeMin),xycoords='data',color='yellow')
    #, xytext=(3, 4),
    #        arrowprops=dict(facecolor='black', shrink=0.05))
    ax.legend(loc=2,prop={'size': 10})
    plt.figtext(0.92, 0.5, 'https://twitter.com/autokorrekturKA', fontsize=8,rotation=270)
#    plt.figtext(0.55, 0.02, '*: Mindestangaben: Nicht alle Parkhäuser\nmelden immer. V.a. Vakanzangaben fehlen häufig.', fontsize=8)
    plt.figtext(0.02, 0.02, '* Nicht alle Parkhäuser melden immer, v.a. Vakanzangaben fehlen häufig. Tatsächliche Werte also meist höher.', fontsize=8)
    # set axis ranges
    yMax = (int(capacityMax/1000)+2)*1000
    ax.set_ylim(0,yMax)
    ax.set_xlim(startTime,endTime)
    # x axis labels (time)
    ax.xaxis.set_major_locator(DayLocator())
    ax.xaxis.set_major_formatter(DateFormatter("%d.%m.%y"))
    ax.xaxis.set_minor_locator(HourLocator(interval=3))
    ax.xaxis.set_minor_formatter(DateFormatter("%H:00"))
    ax.xaxis.grid(True, which='minor')
#    x_dates_str = dfplot['datetime'].dt.strftime('%d.%m. %H:00')
#    ax.set_xticklabels(labels=x_dates_str, rotation=45, ha='right')
#    ax.xaxis.set_major_locator(WeekdayLocator(interval=1))
#    ax.xaxis.set_major_formatter(DateFormatter("%d.%m"))
#    ax.xaxis.set_minor_locator(HourLocator(interval=3))
#    ax.xaxis.set_minor_formatter(DateFormatter("%d.%m %Hh"))
#    ax.format_xdata = DateFormatter('%m.%d. %H')
#    ax.set_xticklabels(labels=x_dates_str, rotation=45, ha='right')
    fig.autofmt_xdate()
#    plt.show()
    # save to file
    plt.savefig(dailyPlotFile)

    # done: return min free
    return freeMin
    

def assemble_message(parkingFreeTotal,parkingCapacityTotal,parkplatzFlaeche,vergleichsFlaechen,familyAppArea,alternativeUseAreas,statements,hashtags,option):
    # imports
    from random import choice
    from datetime import datetime
    
    # computations
    parkingFreeFraction = parkingFreeTotal / parkingCapacityTotal
    parkingFreeArea = parkingFreeTotal*parkplatzFlaeche
    now = datetime.now()
    thisTime = now.strftime("%H:%M")
    
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
        option = choice([1,2,3,4,5])
    
    ## fraction, comparison to popular space
    if option <= 2:
        messageBody = "Im Zentrum von #Karlsruhe sind jetzt "+str(int(parkingFreeTotal))+" von " + str(int(parkingCapacityTotal))+" Auto-Parkhausplätzen ungenutzt ("+str(int(parkingFreeFraction*100))+"%). Für weitere Autos freigehalten: " + str(int(parkingFreeTotal*parkplatzFlaeche)) + "m2 = "+str(round(parkingFractionComp,1)).replace('.',',')+" mal "+vergleichsName+"."
        statement = choice(statements)
        hashtag = choice(hashtags)

    ## free area, comparison to alternative use
    elif option <= 4:
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
    elif option == 5:
        messageBody = "#Karlsruhe lockt Autos ins Herz der Stadt: Um "+thisTime+ " Uhr sind Parkhäuser mit einer Kapazität von " + str(int(parkingCapacityTotal))+" Plätzen geöffnet. Auf diesen etwa " + str(int(parkingCapacityTotal*parkplatzFlaeche))+"m2 könnte man " + str(int(parkingCapacityTotal*parkplatzFlaeche/familyAppArea)) + " Familienwohnungen mit je "+str(familyAppArea)+"m2 unterbringen."
        statement = choice(['Prioritäten...',''])
        hashtag = choice(['#StaedteFuerMenschen','#Wohnungsnot','#Autostadt'])
    
    # assemble
    theMessage = messageBody + ' ' + statement + " " + hashtag

    # done
    return theMessage


## what time is it?
now = datetime.now()
current_time = now.strftime("%Y-%m-%d %H:%M:%S")
thisHour = int(now.strftime("%H"))
todayMidnight = datetime(now.year,now.month,now.day,0,10,0)


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
    option = 5  # message to print
    doTweet = False # stop tweeting
    
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

if thisHour == dailyFigHour:
    minFree = plot_daily(dataFile,dailyPlotFile)
    if minFree >= dailyFigMinFreeLimit:
        if doTweet:
            twitter = Twython(
                consumer_key,
                consumer_secret,
                access_token,
                access_token_secret
            )
            photo = open(dailyPlotFile, 'rb')
            response = twitter.upload_media(media=photo)
            twitter.update_status(status="In den letzten 24 Stunden waren immer mindestens " + str(int(minFree)) + " Parkhausplätze im Zentrum von #Karlsruhe frei - sprich: überflüssig. Wo sind die überdachten Fahrradbügel? #autostadt #Verkehrswende jetzt", media_ids=[response['media_id']])


exit()

