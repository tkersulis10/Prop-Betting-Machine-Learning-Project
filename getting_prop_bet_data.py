# getting points prop bet data starting from 01/06/2021
# activate virtual environment before using: source venv/bin/activate on linux

import time
from selenium import webdriver
from bs4 import BeautifulSoup

def get_data(stat, date_list=None):
    """
    Data scrapes the prop betting lines for all available props for NBA players
    for stat from Jan 1, 2022 to May 31, 2023. If date_list is given, then
    only scrapes those dates. Dates must be in (year, month, day).
    """
    # Main URL for prop bets
    main_url = "https://www.bettingpros.com/nba/odds/player-props/" + stat + "/?date="

    # Set initial date
    date_year = 2021
    date_month = 1
    date_day = 6

    # Chrome webdriver options
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')

    # Different driver paths per computer
    driver_paths = ['/home/tkersulis/cs4701/project/chromedriver.exe', "/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome"]
    driver = webdriver.Chrome(executable_path=driver_paths[0], options=options)

    # Open output file
    file_name = stat + "_prop_bet_output.txt"
    with open(file_name, "a") as file:
        if date_list == None:
            # Loop through years, months, and days
            for year in range(2022, 2024):
                if year == 2023:
                    end_month = 6
                else:
                    end_month = 13
                for month in range(1, end_month):
                    # Determine the number of days in the month
                    days_in_month = 31 if month in [1, 3, 5, 7, 8, 10, 12] else (28 if month == 2 else 30)

                    for day in range(1, days_in_month + 1):
                        # Construct the URL for the specific date
                        url = main_url + f"{year}-{month:02d}-{day:02d}"

                        # Load the URL in the webdriver
                        driver.get(url)
                        time.sleep(2)

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
                            player_name = player.find("a", class_="odds-player__heading")
                            line = player.find("span", class_="odds-cell__line")
                            odds = player.find("span", class_="odds-cell__cost")
                            prop_list.append((player_name.text.strip(), line.text.strip(), odds.text.strip()))

                        # Write prop bets data to the output file
                        date_string = f"Date: {month}-{day}-{year}\n"
                        file.write(date_string)

                        for line in prop_list:
                            line_string = f"Player: {line[0]}, line: {line[1]}, odds: {line[2]}\n"
                            file.write(line_string)

                        file.write("\n")
        else:
            for date in date_list:
                year = date[0]
                month = date[1]
                day = date[2]
                url = main_url + f"{year}-{month:02d}-{day:02d}"

                # Load the URL in the webdriver
                driver.get(url)
                time.sleep(2)

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
                    player_name = player.find("a", class_="odds-player__heading")
                    line = player.find("span", class_="odds-cell__line")
                    odds = player.find("span", class_="odds-cell__cost")
                    prop_list.append((player_name.text.strip(), line.text.strip(), odds.text.strip()))

                # Write prop bets data to the output file
                date_string = f"Date: {month}-{day}-{year}\n"
                file.write(date_string)

                for line in prop_list:
                    line_string = f"Player: {line[0]}, line: {line[1]}, odds: {line[2]}\n"
                    file.write(line_string)

                file.write("\n")

# get_data("points")
# get_data("assists")
get_data("rebounds")