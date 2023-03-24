# Getting game logs for players in the top 200 in points per game for the
# last 3 NBA seasons

import time
from selenium import webdriver
from bs4 import BeautifulSoup
from selenium.common.exceptions import TimeoutException

# Read input file containing player information
input_file = open("points_real_stat_output.txt", 'r')
file_lines = input_file.readlines()

player_link_dict = {}
player_gamelog_dict = {}

# Process each line to get player name and link, then add them to dictionaries
for line in file_lines[0:2]:
    comma_index = line.index(",")
    player_name = line[8:comma_index]
    player_link = line[comma_index + 8:comma_index + 17]
    player_link_dict[player_name] = player_link
    player_gamelog_dict[player_name] = []

input_file.close()

# Define URL components
base_url = "https://www.basketball-reference.com/players/"
gamelog_url = "/gamelog/"

# Configure Selenium WebDriver
options = webdriver.ChromeOptions()
options.add_argument('--headless')
driver_paths = ['/home/tkersulis/cs4701/project/chromedriver.exe', "/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome"]
driver = webdriver.Chrome(executable_path=driver_paths[0], options=options)
driver.set_page_load_timeout(30)

# Open output file
output_file = open("player_gamelog_output.txt", "a")

# Iterate through years and players to collect game logs
for year in range(2021, 2024):
    for player in player_link_dict:
        space_index = player.index(" ")
        player_initial = player[space_index + 1: space_index + 2]
        player_link = player_link_dict[player]
        url = base_url + player_initial + "/" + player_link + gamelog_url + str(year)
        
        # Try to load the URL and catch timeouts
        try:
            driver.get(url)
        except TimeoutException:
            pass
        time.sleep(2)

        # Parse HTML using BeautifulSoup
        html_source = driver.page_source
        soup = BeautifulSoup(html_source, "html.parser")

        # Extract game logs
        results = soup.find('table', id='pgl_basic')
        game_rows = results.find_all("tr", id=lambda x: x and x.startswith('pgl_basic'))
        
        # Iterate through game rows and collect stats
        for row in game_rows:
            date = row.find('td', {'data-stat': 'date_game'}).text
            points = row.find('td', {'data-stat': 'pts'}).text
            rebounds = row.find('td', {'data-stat': 'trb'}).text
            assists = row.find('td', {'data-stat': 'ast'}).text
            player_gamelog_dict[player].append((date, points, rebounds, assists))

# Write the game logs to the output file
for player in player_gamelog_dict:
    output_file.write(player + ":\n")
    for game in player_gamelog_dict[player]:
        game_string = f"Date: {game[0]}, pts: {game[1]}, rbs: {game[2]}, ast: {game[3]}\n"
        output_file.write(game_string)
    output_file.write("\n")

output_file.close()