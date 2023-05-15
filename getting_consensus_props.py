from selenium import webdriver
chrome_options = webdriver.ChromeOptions()
chrome_options.add_argument('--headless')

import time
from selenium import webdriver
from bs4 import BeautifulSoup
import json

driver = webdriver.Chrome('chromedriver',options=chrome_options)

# Main URL for prop bets
main_url = "https://www.bettingpros.com/nba/odds/player-props/assists/?date="

# Set initial date
date_year = 2021
date_month = 1
date_day = 6

# Chrome webdriver options
# options = webdriver.ChromeOptions()
# options.add_argument('--headless')

# Different driver paths per computer
driver_paths = ['/home/tkersulis/cs4701/project/chromedriver.exe', "/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome"]
driver = webdriver.Chrome(executable_path=driver_paths[1], options=options)

# Open output file
with open("assists_prop_lines2021.txt", "a") as file:
    # Loop through years, months, and days
    for year in range(2021, 2022):
        for month in range(1, 13):
            # Determine the number of days in the month
            days_in_month = 31 if month in [1, 3, 5, 7, 8, 10, 12] else (28 if month == 2 else 30)
            if (month >= 7):
                nba_year = year+1
            else:
                nba_year = year
            for day in range(1, days_in_month + 1):
                # Construct the URL for the specific date
                url = main_url + f"{year}-{month:02d}-{day:02d}"

                # Load the URL in the webdriver
                print(url)
                driver.get(url)
                time.sleep(5)

                # Scrolling implementation:
                # Credit: https://medium.com/analytics-vidhya/using-python-and-selenium-to-scrape-infinite-scroll-web-pages-825d12c24ec7
                scrolling_wait = 1
                website_height = driver.execute_script("return window.screen.height;")
                i = 1
                keep_scrolling = True

                while keep_scrolling:
                    driver.execute_script("window.scrollTo(0, {screen_height}*{i});".format(screen_height=website_height, i=i))
                    i += 1
                    time.sleep(scrolling_wait)
                    scroll_height = driver.execute_script("return document.body.scrollHeight;")
                    if website_height * i > scroll_height:
                        keep_scrolling = False

                # Parse the HTML content
                htmlSource = driver.page_source
                soup = BeautifulSoup(htmlSource, "html.parser")

                # Extract player prop bets data
                results = soup.find(id="odds-app")
                prop_list = []
                players = results.find_all("div", class_="grouped-items-with-sticky-footer__content")

                for player in players:
                  try:
                    player_name_abbreviated = player.find("a", class_="odds-player__heading").text
                    player_name_link = player.find("a", class_="odds-player__heading", href=True).get('href')
                    player_name_raw = "".join(player_name_link.split("/")[-2].split("-", 1))
                    player_team = player.find("p", class_="odds-player__subheading").text.split()[0].lower()
                    player_name = player_name_raw + str(nba_year)
                    lines = {}
                    # print(player.prettify())
                    offerrings = player.findAll("div", class_="odds-offer__item")
                    print(len(offerrings))
                    o_line = offerrings[-1].findAll("span", class_="odds-cell__line")[0].text.strip()
                    if (o_line == "NL" or o_line == "OFF"):
                        continue
                    o_odds = offerrings[-1].findAll("span", class_="odds-cell__cost")[0].text.strip().strip("+()")
                    if (o_odds.lower() == "even"):
                        o_odds = "100"
                    u_line = offerrings[-1].findAll("span", class_="odds-cell__line")[1].text.strip()
                    if (u_line == "NL" or u_line == "OFF"):
                        continue
                    u_odds = offerrings[-1].findAll("span", class_="odds-cell__cost")[1].text.strip().strip("+()")
                    if (u_odds.lower() == "even"):
                        u_odds = "100"
                    o_line = o_line.split()[-1]
                    u_line = u_line.split()[-1]
                    lines["consensus"] = [o_line+"@"+o_odds, u_line+"@"+u_odds]
                    for i, offerring in enumerate(offerrings):
                        # print(offerring.text)
                        if offerring['class'][-1] in ["odds-offer__item--best-odds", "odds-offer__item--open", "odds-offer__item--first"]:
                            continue
                        if i == len(offerrings)-1:
                          continue
                        # print(offerring['class'])
                        o_line = offerring.findAll("span", class_="odds-cell__line")[0].text.strip()
                        if (o_line == "NL" or o_line == "OFF"):
                            continue
                        o_odds = offerring.findAll("span", class_="odds-cell__cost")[0].text.strip().strip("+()")
                        if (o_odds.lower() == "even"):
                            o_odds = "100"
                        u_line = offerring.findAll("span", class_="odds-cell__line")[1].text.strip()
                        if (u_line == "NL" or u_line == "OFF"):
                            continue
                        u_odds = offerring.findAll("span", class_="odds-cell__cost")[1].text.strip().strip("+()")
                        if (u_odds.lower() == "even"):
                            u_odds = "100"
                        o_line = o_line.split()[-1]
                        u_line = u_line.split()[-1]
                        if o_line not in lines:
                            lines[o_line] = [int(o_odds), int(u_odds)]
                        else:
                          try:
                            o_odds_optimal = max(lines[o_line][0], int(o_odds))
                            u_odds_optimal = max(lines[u_line][1], int(u_odds))
                            lines[o_line] = [o_odds_optimal, u_odds_optimal]
                          except:
                            continue

                    # line = player.find("span", class_="odds-cell__line")
                    # odds = player.find("span", class_="odds-cell__cost")
                    d = json.dumps({"Player": player_name, "lines": json.dumps(lines)})
                    print(d)
                    prop_list.append(d)
                  except:
                    continue

                # Write prop bets data to the output file
                date_string = f"Date: {month}-{day}-{year}\n"
                file.write(date_string)

                for line in prop_list:
                    # line_string = f"Player: {line[0]}, line: {line[1]}, odds: {line[2]}\n"
                    # line_string = f"Player: {line[0]}, lines: {line[1]}\n"
                    # print(line)
                    file.write(line + "\n")

                file.write("\n")