import requests
from bs4 import BeautifulSoup

class Location:
    def __init__(self, zip):
        self.zip = zip

    def getWeather(self):
        # create url
        url = "https://www.google.com/search?q=" + "weather" + self.zip
        # requests instance
        html = requests.get(url).content
        # getting raw data
        soup = BeautifulSoup(html, 'html.parser')
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
        print("Time: ", time)
        print("Sky Description: ", sky)

        return temp, weekday, time, sky