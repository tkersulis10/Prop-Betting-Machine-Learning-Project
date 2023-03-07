# getting points real data for top 200 points per game players in the 2020/21
# 2021/22, and 2022/23 NBA seasons
# activate virtual environment before using: source venv/bin/activate on linux

import time
from selenium import webdriver
from bs4 import BeautifulSoup
import requests
from selenium.common.exceptions import TimeoutException

# url_2020_2021 = "https://www.basketball-reference.com/leagues/NBA_2021_per_game.html#per_game_stats::pts_per_g"
first_url = "https://www.basketball-reference.com/leagues/NBA_"
second_url = "_per_game.html#per_game_stats::pts_per_g"
date_year = 2021

options = webdriver.ChromeOptions()
options.add_argument('--headless')
driver = webdriver.Chrome(
    executable_path='/home/tkersulis/cs4701/project/chromedriver.exe', options=options)
driver.set_page_load_timeout(30)

# LOOP
file = open("points_real_stat_output.txt", "a")
player_dict = {}
for year in range(2021, 2024):
    url = first_url + str(year) + second_url
    try:
        driver.get(url)
    except TimeoutException:
        pass
    time.sleep(2)

    htmlSource = driver.page_source
    soup = BeautifulSoup(htmlSource, "html.parser")

    # results = soup.find(id="all_per_game_stats")
    results = soup.find('table')

    player_rows = results.find_all("tr", class_="full_table")
    player_rows = player_rows[:200]
    for row in player_rows:
        player = row.find('td', {'data-stat': 'player'})
        player_link = player['data-append-csv']
        player_name = player.text
        player_dict[player_name] = player_link

for player in player_dict:
    player_string = "Player: " + \
        str(player) + ", link: " + str(player_dict[player])
    file.write(player_string)
    file.write("\n")
file.close()
