# getting points prop bet data starting from 01/06/2021
# activate virtual environment before using: source venv/bin/activate on linux

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
file = open("points_prop_bet_output.txt", "a")
# file.write("Points from 01-06-2021 to 12-31-2022\n")
for year in range(2021, 2023):
    for month in range(1, 13):
        if month == 1 or month == 3 or month == 5 or month == 7 or month == 8 or month == 10 or month == 12:
            days_in_month = 31
        elif month == 2:
            days_in_month = 28
        else:
            days_in_month = 30
        for day in range(1, days_in_month + 1):
            if month < 10:
                if day < 10:
                    url = main_url + str(year) + "-0" + \
                        str(month) + "-0" + str(day)
                else:
                    url = main_url + str(year) + "-0" + \
                        str(month) + "-" + str(day)
            else:
                if day < 10:
                    url = main_url + str(year) + "-" + \
                        str(month) + "-0" + str(day)
                else:
                    url = main_url + str(year) + "-" + \
                        str(month) + "-" + str(day)
            driver.get(url)
            time.sleep(2)

            # scrolling implementation credit:
            # https://medium.com/analytics-vidhya/using-python-and-selenium-to-scrape-infinite-scroll-web-pages-825d12c24ec7
            scrolling_wait = 1
            website_height = driver.execute_script(
                "return window.screen.height;")
            i = 1
            keep_scrolling = True
            while keep_scrolling:
                driver.execute_script(
                    "window.scrollTo(0, {screen_height}*{i});".format(screen_height=website_height, i=i))
                i += 1
                time.sleep(scrolling_wait)
                scroll_height = driver.execute_script(
                    "return document.body.scrollHeight;")
                if website_height * i > scroll_height:
                    keep_scrolling = False

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
            date_string = "Date: " + str(month) + "-" + \
                str(day) + "-" + str(year) + "\n"
            file.write(date_string)
            for line in prop_list:
                line_string = "Player: " + line[0] + \
                    ", line: " + line[1] + ", odds: " + line[2] + "\n"
                file.write(line_string)
            file.write("\n")
file.close()
