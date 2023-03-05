# getting points prop bet data starting from 01/06/2021

import time
from selenium import webdriver
from bs4 import BeautifulSoup
import requests
# my_url = "https://www.bettingpros.com/nba/odds/player-props/points/?date=2021-01-06"
main_url = "https://www.bettingpros.com/nba/odds/player-props/points/?date="
date_year = 2021
date_month = 1
date_day = 6

options = webdriver.ChromeOptions()
options.add_argument('--headless')
driver = webdriver.Chrome(
    executable_path='/home/tkersulis/cs4701/project/chromedriver.exe', options=options)


# LOOP
for day in range(date_day, 32):
    if date_month < 10:
        if day < 10:
            url = main_url + str(date_year) + "-0" + \
                str(date_month) + "-0" + str(day)
        else:
            url = main_url + str(date_year) + "-0" + \
                str(date_month) + "-" + str(day)
    else:
        if day < 10:
            url = main_url + str(date_year) + "-" + \
                str(date_month) + "-0" + str(day)
        else:
            url = main_url + str(date_year) + "-" + \
                str(date_month) + "-" + str(day)
    driver.get(url)
    time.sleep(2)
    htmlSource = driver.page_source
    soup = BeautifulSoup(htmlSource, "html.parser")

    results = soup.find(id="odds-app")

    prop_list = []
    players = results.find_all(
        "div", class_="grouped-items-with-sticky-footer__content")
    for player in players:
        player_name = player.find("a", class_="odds-player__heading")
        line = player.find("span", class_="odds-cell__line")
        odds = player.find("span", class_="odds-cell__cost")
        prop_list.append(
            (player_name.text.strip(), line.text.strip(), odds.text.strip()))

    # print(prop_list)
    file = open("output.txt", "a")
    date_string = "Date: " + str(date_month) + "-" + \
        str(day) + "-" + str(date_year) + "\n"
    file.write(date_string)
    for line in prop_list:
        line_string = "Player: " + line[0] + \
            ", line: " + line[1] + ", odds: " + line[2] + "\n"
        file.write(line_string)
    file.write("\n")
file.close()
