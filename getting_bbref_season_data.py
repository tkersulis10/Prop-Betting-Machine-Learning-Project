import time
from bs4 import BeautifulSoup
import requests
from unidecode import unidecode
import json
import pickle

player_identifier_to_object = {}

def make_request(url):
    # bbref only lets you make max 20 requests per minute, otherwise it will block you
    time.sleep(3)
    return requests.get(url)

class Season:
    def __init__(self, year):
        self.year = year
        self.games = {}
        self.teams = {
            "ATL": 0,
            "BOS": 0,
            "BRK": 0,
            "CHO": 0,
            "CHI": 0,
            "CLE": 0,
            "DAL": 0,
            "DEN": 0,
            "DET": 0,
            "GSW": 0,
            "HOU": 0,
            "IND": 0,
            "LAC": 0,
            "LAL": 0,
            "MEM": 0,
            "MIA": 0,
            "MIL": 0,
            "MIN": 0,
            "NOP": 0,
            "NYK": 0,
            "OKC": 0,
            "ORL": 0,
            "PHI": 0,
            "PHO": 0,
            "POR": 0,
            "SAC": 0,
            "SAS": 0,
            "TOR": 0,
            "UTA": 0,
            "WAS": 0,
        }
    def __repr__(self):
        return str(self.__dict__)
    def getTeams(self):
        for team_name in list(self.teams.keys()):
            games_so_far = list(self.games.keys())
            team = Team(self.year, team_name)
            url = "https://www.basketball-reference.com/teams/" + team_name + "/" + str(self.year) + ".html"
            soup = BeautifulSoup(make_request(url).content, "html.parser")
            # print(soup.prettify())
            players = soup.find(id="div_roster").find("tbody").find_all("tr")
            for player in players:
                bbref_player_link = player.find('a', href=True)
                # actual link is of the form: /players/y/youngtr01.html 
                # bbref_name of the form y/youngtr01
                bbref_name = bbref_player_link.get('href')[9:-5]
                # identifier of the form "traeyoung2020ATL"
                name = bbref_player_link.getText()
                identifier = unidecode("".join(bbref_player_link.getText().split())) + str(self.year) + team_name

                player_attributes = player.find_all("td")
                player_position = 0
                player_experience = 0
                for attribute in player_attributes:
                    if attribute.get('data-stat') == "pos":
                        player_position = attribute.get('csk')
                    elif attribute.get('data-stat') == "years_experience":
                        player_experience = attribute.get('csk')
                newplayer = Player(self.year, team, bbref_name, name, identifier, player_position, player_experience)
                player_identifier_to_object[identifier] = newplayer
                team.players.append(newplayer)

            print("starting to collect games")
            games_url = url = "https://www.basketball-reference.com/teams/" + team_name + "/" + str(self.year) + "_games.html"
            print(games_url)
            soup = BeautifulSoup(make_request(games_url).content, "html.parser")
            games = soup.find(id="div_games").find("tbody").find_all("tr")
            # print(len(games))
            for game in games:
                th = game.find("th")
                if (th.get("scope") != "row"):
                    continue
                links = game.find_all('a', href=True)
                date = links[0].getText()
                game_url = "https://www.basketball-reference.com" + links[1].get('href')
                game_id = game_url[11:-5]
                # print(game_id)
                if game_id in games_so_far:
                    current_game = self.games[game_id]
                else:
                    current_game = Game(date, self.year, game_id)
                game_no = game.find('th').getText()
                home = False
                if team_name in game_url:
                    home = True
                game_soup = BeautifulSoup(make_request(game_url).content, "html.parser")
                basic_stats_table = game_soup.find(id="box-"+team_name+"-game-basic")
                basic_stats = []
                stats = basic_stats_table.find("thead").find_all("tr")[-1].find_all("th")[1:]
                for stat in stats:
                    basic_stats.append(stat.get("data-stat"))

                tbody_rows = basic_stats_table.find("tbody").find_all("tr")
                starter_bbrefs = []
                reserve_bbrefs = []
                box_score = {}

                starters = tbody_rows[:5]
                for starter in starters:
                    bbref = starter.find('a', href=True).get('href')[9:-5]
                    starter_bbrefs.append(bbref)
                    stat_map = {}
                    player_stats = starter.find_all("td")
                    if (len(player_stats) == 1):
                        box_score[bbref] = "DNP"
                        continue
                    for i, stat_value in enumerate(player_stats):
                        stat_map[basic_stats[i]] = stat_value.getText()
                    box_score[bbref] = stat_map

                reserves = tbody_rows[6:]
                for reserve in reserves:
                    bbref = reserve.find('a', href=True).get('href')[9:-5]
                    reserve_bbrefs.append(bbref)
                    stat_map = {}
                    player_stats = reserve.find_all("td")
                    if (len(player_stats) == 1):
                        box_score[bbref] = "DNP"
                        continue                    
                    for i, stat_value in enumerate(player_stats):
                        stat_map[basic_stats[i]] = stat_value.getText()
                    box_score[bbref] = stat_map

                advanced_stats_table = game_soup.find(id="box-"+team_name+"-game-advanced")
                advanced_stats = []
                stats = advanced_stats_table.find("thead").find_all("tr")[-1].find_all("th")[1:]
                for stat in stats:
                    advanced_stats.append(stat.get("data-stat"))

                tbody_rows = advanced_stats_table.find("tbody").find_all("tr")

                starters = tbody_rows[:5]
                for starter in starters:
                    bbref = starter.find('a', href=True).get('href')[9:-5]
                    stat_map = box_score[bbref]
                    player_stats = starter.find_all("td")
                    if (len(player_stats) == 1):
                        continue
                    for i, stat_value in enumerate(player_stats):
                        try:
                            stat_map[advanced_stats[i]] = stat_value.getText()
                        except:
                            print(stat_map)
                    box_score[bbref] = stat_map

                reserves = tbody_rows[6:]
                for reserve in reserves:
                    bbref = reserve.find('a', href=True).get('href')[9:-5]
                    stat_map = box_score[bbref]
                    player_stats = reserve.find_all("td")
                    if (len(player_stats) == 1):
                        continue                    
                    for i, stat_value in enumerate(player_stats):
                        stat_map[advanced_stats[i]] = stat_value.getText()
                    box_score[bbref] = stat_map

                inactives = []
                for p in team.players:
                    if p.bbref_name not in starter_bbrefs and p.bbref_name not in reserve_bbrefs:
                        inactives.append(p.bbref_name)
                        p.gamelog.append("IN")
                    else:
                        p.gamelog.append(box_score[p.bbref_name])

                if (home):
                    current_game.home_team = team_name
                    current_game.home_team_game_no = game_no
                    current_game.home_inactives = inactives
                    current_game.home_reserves = reserve_bbrefs
                    current_game.home_starters = starter_bbrefs
                    current_game.home_player_stats = box_score
                else:
                    current_game.away_team = team_name
                    current_game.away_team_game_no = game_no
                    current_game.away_inactives = inactives
                    current_game.away_reserves = reserve_bbrefs
                    current_game.away_starters = starter_bbrefs
                    current_game.away_player_stats = box_score

                self.games[game_id] = current_game
                team.games.append(current_game)

            
            self.teams[team_name] = team
            # print(team.__dict__)
            


class Team:
    def __init__(self, year, name):
        self.year = year
        self.name = name
        self.players = []
        self.games = []
    def __repr__(self):
        return str(self.__dict__)

class Game:
    def __init__(self, date, year, id):
        self.date = date
        self.year = year
        self.id = id
        self.home_team = ""
        self.away_team = ""
        self.home_team_game_no = 0
        self.away_team_game_no = 0
        self.home_starters = []
        self.home_reserves = []
        self.home_inactives = []
        self.away_starters = []
        self.away_reserves = []
        self.away_inactives = []
        self.home_player_stats = {}
        self.away_player_stats = {}
    def __repr__(self):
        return str(self.__dict__)


class Player:
    def __init__(self, year, team, bbref_name, name, identifier, position, exp):
        self.bbref_name = bbref_name
        self.name = name
        self.team = team
        self.year = year
        self.identifier = identifier
        self.exp = exp
        self.position = position
        self.gamelog = []
        # TODO: decide how to encode a player's most recent healthy season
        self.most_recent_valid_season = {}
    def __repr__(self):
        return str(self.__dict__)

# To get a season's data
s2020 = Season(2020)
s2020.getTeams()
# To save objects to a file
with open('s2020.pkl', 'wb') as outp:
    pickle.dump(s2020, outp, pickle.HIGHEST_PROTOCOL)

s2021 = Season(2021)
s2021.getTeams()
with open('s2021.pkl', 'wb') as outp:
    pickle.dump(s2021, outp, pickle.HIGHEST_PROTOCOL)

s2022 = Season(2022)
s2022.getTeams()
with open('s2022.pkl', 'wb') as outp:
    pickle.dump(s2022, outp, pickle.HIGHEST_PROTOCOL)

s2023 = Season(2023)
s2023.getTeams()
with open('s2023.pkl', 'wb') as outp:
    pickle.dump(s2023, outp, pickle.HIGHEST_PROTOCOL)

with open('players.pkl', 'wb') as outp:
    pickle.dump(player_identifier_to_object, outp, pickle.HIGHEST_PROTOCOL)

# To load objects from file:
# with open('s2020.pkl', 'rb') as inp:
#     s2020 = pickle.load(inp)
# with open('players.pkl', 'rb') as inp:
#     players = pickle.load(inp)

# example usage after loading:
# example: stephen curry full stat line from first game of the 2020 season
# print(players['StephenCurry2020GSW'].gamelog[0])
