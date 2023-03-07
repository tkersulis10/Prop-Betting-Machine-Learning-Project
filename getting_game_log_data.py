# Getting game logs for players in the top 200 in points per game for the
# last 3 NBA seasons

import time
from selenium import webdriver
from bs4 import BeautifulSoup
import requests
from selenium.common.exceptions import TimeoutException
import re

first_file = open("points_real_stat_output.txt", 'r')
file_lines = first_file.readlines()

player_link_dict = {}
player_gamelog_dict = {}
for line in file_lines[0:2]:
    comma_index = line.index(",")
    player_name = line[8:comma_index]
    player_link = line[comma_index + 8:comma_index + 17]
    player_link_dict[player_name] = player_link
    player_gamelog_dict[player_name] = []

first_file.close()
first_url = "https://www.basketball-reference.com/players/"
second_url = "/gamelog/"
year_url = "2021"

options = webdriver.ChromeOptions()
options.add_argument('--headless')
driver = webdriver.Chrome(
    executable_path='/home/tkersulis/cs4701/project/chromedriver.exe', options=options)
driver.set_page_load_timeout(30)

file = open("player_gamelog_output.txt", "a")
for year in range(2021, 2024):
    for player in player_link_dict:
        space_index = player.index(" ")
        player_initial_url = player[space_index + 1: space_index + 2]
        player_link_url = player_link_dict[player]
        url = first_url + player_initial_url + "/" + \
            player_link_url + second_url + str(year)
        try:
            driver.get(url)
        except TimeoutException:
            pass
        time.sleep(2)

        htmlSource = driver.page_source
        soup = BeautifulSoup(htmlSource, "html.parser")

        results = soup.find('table', id='pgl_basic')

        game_rows = results.find_all(
            "tr", id=lambda x: x and x.startswith('pgl_basic'))
        for row in game_rows:
            date = row.find('td', {'data-stat': 'date_game'}).text
            points = row.find('td', {'data-stat': 'pts'}).text
            rebounds = row.find('td', {'data-stat': 'trb'}).text
            assists = row.find('td', {'data-stat': 'ast'}).text
            player_gamelog_dict[player].append(
                (date, points, rebounds, assists))

for player in player_gamelog_dict:
    file.write(player + ":\n")
    for game in player_gamelog_dict[player]:
        game_string = "Date: " + str(game[0]) + ", pts: " + str(
            game[1]) + ", rbs: " + str(game[2]) + ", ast: " + str(game[3]) + "\n"
        file.write(game_string)
    file.write("\n")
file.close()
