import requests
import bs4
import time

class Location:
    def __init__(self, zip):
        self.zip = zip

    @property
    def getWeather(self):
        # create url
        url = "https://www.google.com/search?q=" + "weather" + self.zip
        # requests instance
        html = requests.get(url).content
        # getting raw data
        soup = bs4.BeautifulSoup(html, 'html.parser')
        temp = soup.find('div', attrs={'class': 'BNeawe iBp4i AP7Wnd'}).text
        str = soup.find('div', attrs={'class': 'BNeawe tAd8D AP7Wnd'}).text

        # formatting data
        data = str.split('\n')
        tempList = temp.split("°")
        timeList = data[0].split()
        sky = data[1]

        temp = tempList[0]
        weekday = timeList[0]
        time = timeList[1] + " " + timeList[2]

        # printing all data
        print("Temperature is", temp)
        print("Weekday is", weekday)
        print("Sky Description: ", sky)

        return temp, weekday, sky

    def getTime(self):

        t = time.localtime(time.time())

        timeFrame = "unlisted"
        if (t.tm_hour >= 5 & t.tm_hour < 11):
            timeFrame = "Morning"
        if (t.tm_hour >= 11 & t.tm_hour < 17):
            timeFrame = "Midday"
        if (t.tm_hour >= 17 & t.tm_hour < 23):
            timeFrame = "Evening"
        else:
            timeFrame = "Night"

        return ("songsPlayed" + timeFrame + ".txt")