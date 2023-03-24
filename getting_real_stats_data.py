# getting points real data for top 200 points per game players in the 2020/21
# 2021/22, and 2022/23 NBA seasons
# activate virtual environment before using: source venv/bin/activate on linux

import time
from selenium import webdriver
from bs4 import BeautifulSoup
from selenium.common.exceptions import TimeoutException

# Base URLs for constructing the request URL
first_url = "https://www.basketball-reference.com/leagues/NBA_"
second_url = "_per_game.html#per_game_stats::pts_per_g"

# Configure Chrome webdriver options
options = webdriver.ChromeOptions()
options.add_argument('--headless')

# Change the driver path based on your computer setup
driver_paths = ['/home/tkersulis/cs4701/project/chromedriver.exe', "/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome"]
driver = webdriver.Chrome(executable_path=driver_paths[0], options=options)
driver.set_page_load_timeout(30)

# Initialize the dictionary to store player names and links
player_dict = {}

# Loop through the NBA seasons from 2021 to 2023
for year in range(2021, 2024):
    url = first_url + str(year) + second_url
    try:
        driver.get(url)
    except TimeoutException:
        pass
    time.sleep(2)

    # Parse the HTML content
    htmlSource = driver.page_source
    soup = BeautifulSoup(htmlSource, "html.parser")

    # Find the table containing the player stats
    results = soup.find('table')

    # Extract the rows containing the top 200 players
    player_rows = results.find_all("tr", class_="full_table")
    player_rows = player_rows[:200]
    
    # Iterate through the rows and store player names and links in the dictionary
    for row in player_rows:
        player = row.find('td', {'data-stat': 'player'})
        player_link = player['data-append-csv']
        player_name = player.text
        player_dict[player_name] = player_link

# Write the player names and links to a file
with open("points_real_stat_output.txt", "a") as file:
    for player in player_dict:
        player_string = f"Player: {player}, link: {player_dict[player]}"
        file.write(player_string)
        file.write("\n")