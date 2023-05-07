import time
from bs4 import BeautifulSoup
import requests
from unidecode import unidecode
import pickle
import json
from selenium import webdriver
import traceback

player_identifier_to_object = {}

def make_request(url):
    """
    Make a request to the given URL after waiting for 3 seconds to avoid hitting the rate limit.
    """
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

            # Collect players data
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

                team_box_score = {}
                tfoot_row = basic_stats_table.find("tfoot").find("tr")
                team_basic_stats = tfoot_row.find_all("td")
                for i, stat_value in enumerate(team_basic_stats):
                    team_box_score[basic_stats[i]] = stat_value.getText()

                tfoot_row = advanced_stats_table.find("tfoot").find("tr")
                team_advanced_stats = tfoot_row.find_all("td")
                for i, stat_value in enumerate(team_advanced_stats):
                    team_box_score[advanced_stats[i]] = stat_value.getText()

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
                    current_game.home_team_stats = team_box_score
                else:
                    current_game.away_team = team_name
                    current_game.away_team_game_no = game_no
                    current_game.away_inactives = inactives
                    current_game.away_reserves = reserve_bbrefs
                    current_game.away_starters = starter_bbrefs
                    current_game.away_player_stats = box_score
                    current_game.away_team_stats = team_box_score

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
        self.home_team_stats = {}
        self.away_team_stats = {}
    def __repr__(self):
        return json.dumps(self.__dict__)


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
    
with open('s2022.pkl', 'rb') as inp:
    s2022 = pickle.load(inp)

with open('players.pkl', 'rb') as inp:
    players = pickle.load(inp)

def extract_stat_from_log(stat, log):
    return [0.0 if game=="DNP" else float(game[stat]) for game in log]

def get_percentiles(totals, percentiles):
    results = []
    totals.sort()
    cume = 0.0
    index = 0
    for i in range(len(percentiles)):
        target = percentiles[i]
        while (cume < target):
            index += 1
            cume = index/len(totals)
        results.append(totals[index])
    return results
    
def featurize_instance(player_id, date_string):
    player = players[player_id]
    player_team = player_id[-3:]
    date_split = date_string.split("-")
    year = date_split[2]
    month = date_split[0]
    day = date_split[1]
    if len(month) == 1:
        month = "0" + month
    if len(day) == 1:
        day = "0" + day
    target_game_id_prefix = year+month+day
    games = s2022.teams[player_team].games
    index = -1
    for i, game in enumerate(games):
        if target_game_id_prefix in game.id:
            if player.gamelog[i] == "IN" or player.gamelog[i] == "DNP":
                return ("error", "instance does not exist")
            index = i
            break
    if (index == -1):
        return ("error", "game does not exist")
    if (index <= 7):
        return ("error", "too early")
    feature_vector = []
    prior_list = [0.0, 0.0, 0.0, 0.0, 0.0, float(player.exp)]
    prior_map = player.most_recent_valid_season
    if (prior_map == {}):
        return ("error", "no priors")
    if (len(prior_map) != 17):
        return ("error", "incorrect prior map")
    for category in prior_map:
        if category == "pos":
            prior_list[prior_map['pos']-1] = 1.0
            continue
        if (type(prior_map[category]) == 'bool'):
            print(player_id + " " + category + str(prior_map))
        if len(prior_map[category]) == 0:
            return ("error", "prior map "+category)
        if category == "Height":
            feet_in = prior_map[category].strip("\"\'").split("\'")
            try:
                inches = float(12*int(feet_in[0])) + float(feet_in[1])
                prior_list.append(float(inches))
            except:
                return ("error", "height")
            continue
        if category == "Draft position":
            try:
                prior_list.append(float(prior_map[category]))
            except:
                prior_list.append(float(100))
            continue
        try:
            prior_list.append(float(prior_map[category].strip("%").replace("<1", "0")))
        except:
            print(player_id + " " + category + " " + str(prior_map))
    feature_vector += prior_list
    
    valid_games = []
    num_inactive_games = 0
    for i in range(0, index):
        if (player.gamelog[i] != "IN" and player.gamelog[i] != "DNP"):
            valid_games.append(player.gamelog[i])
        else:
            num_inactive_games+=1

    if len(valid_games) < 8:
        return ("error", "not enough games")
    
    valid_games_copy = valid_games.copy()
    
    feature_vector.append(len(valid_games))
    point_totals = extract_stat_from_log('pts', valid_games)
    fga_totals = extract_stat_from_log('fga', valid_games)
    fg3a_totals = extract_stat_from_log('fg3a', valid_games)
    fg3_totals = extract_stat_from_log('fg3', valid_games)
    mp_totals = [0.0 if game=="DNP" else float(game['mp'].split(":")[0]) for game in valid_games]
    ft_totals = extract_stat_from_log('ft', valid_games)
    fta_totals = extract_stat_from_log('fta', valid_games)
    usg_totals = extract_stat_from_log('usg_pct', valid_games)
    points = sum(point_totals)
    fga = sum(fga_totals)
    fta = sum(fta_totals)
    true_shooting = points/(2 * (fga + 0.44*fta))
    if fta == 0:
        ft_pct = 65.0
    else:
        ft_pct = sum(ft_totals)/fta
    fg3a = sum(fg3a_totals)
    fg3_frequency = fg3a/fga
    ft_frequency = fta/fga
    ppg = points/len(valid_games)
    fga_average = fga/len(valid_games)
    mp = sum(mp_totals)
    mp_average = mp/len(valid_games)

    #Basic cumulative season stats
    season = [true_shooting, ft_pct, fg3_frequency, ft_frequency, ppg, fga_average, mp_average]
    feature_vector += season

    # percentiles: 20, 40, 50, 60, 80, for points, fga, usage, mp
    percentiles = [0.2, 0.4, 0.5, 0.6, 0.8]
    point_percentiles = get_percentiles(point_totals, percentiles)
    fga_percentiles = get_percentiles(fga_totals, percentiles)
    usage_percentiles = get_percentiles(usg_totals, percentiles)
    mp_percentiles = get_percentiles(mp_totals, percentiles)

    feature_vector += point_percentiles
    feature_vector += fga_percentiles
    feature_vector += usage_percentiles
    feature_vector += mp_percentiles

    player_index = index-num_inactive_games

    try:
        recent_form_windows = [1, 2, 4, 8]

        game_count = 0
        points_list = []
        fga_list = []
        usage_list = []
        mp_list = []
        ft_list = []
        fta_list = []
        fg3a_list = []
        for i in range(len(recent_form_windows)):
            while (game_count < recent_form_windows[i]):
                game_count+=1
                idx = player_index - game_count
                points_list.append(float(valid_games_copy[idx]['pts']))
                fga_list.append(float(valid_games_copy[idx]['fga']))
                usage_list.append(float(valid_games_copy[idx]['usg_pct']))
                # mp_list.append(float(valid_games_copy[idx]['mp'].split(":")[0]*60 + valid_games_copy[idx]['mp'].split(":")[1]))
                mp_list.append(float(valid_games_copy[idx]['mp'].split(":")[0]))
                ft_list.append(float(valid_games_copy[idx]['ft']))
                fta_list.append(float(valid_games_copy[idx]['fta']))
                fg3a_list.append(float(valid_games_copy[idx]['fg3']))
            points_list.sort()
            fga_list.sort()
            usage_list.sort()
            mp_list.sort()
            feature_vector+=points_list.copy()
            feature_vector+=fga_list.copy()
            feature_vector+=usage_list.copy()
            feature_vector+=mp_list.copy()
            
            points = sum(points_list)
            fga = sum(fga_list)
            fta = sum(fta_list)
            true_shooting = points/(2 * (fga + 0.44*fta))
            if (fta == 0):
                ft_pct = 65.0
            else:
                ft_pct = sum(ft_list)/fta
            fg3a = sum(fg3a_list)
            fg3_frequency = fg3a/fga
            ft_frequency = fta/fga

            recent_form_averages = [true_shooting, ft_pct, fg3_frequency, ft_frequency]
            feature_vector += recent_form_averages
    except Exception as e:
        print(player_id + date_string +  " error: " + str(e))
        print(traceback.format_exc())
        return ("error", "problem with recent form collection")

    this_game = games[i]
    if player_team == this_game.home_team:
        feature_vector.append(1.0)
        feature_vector.append(this_game.home_team_game_no)
        feature_vector.append(this_game.away_team_game_no)
        opponent = this_game.away_team
        opponent_game_no = this_game.away_team_game_no
    elif player_team == this_game.away_team:
        feature_vector.append(0.0)
        feature_vector.append(this_game.away_team_game_no)
        feature_vector.append(this_game.home_team_game_no)
        opponent = this_game.home_team
        opponent_game_no = this_game.home_team_game_no
    else:
        return ("error", "could not find game")
    
    team_stats_games = []
    for i in range(index):
        current = games[i]
        if current.home_team == player_team:
            team_stats_games.append(current.home_team_stats)
        elif current.away_team == player_team:
            team_stats_games.append(current.away_team_stats)
        else:
            return ("error", "issue with gathering team stats")
        
    off_rtg_totals = sum(extract_stat_from_log('off_rtg', team_stats_games))/index
    def_rtg_totals = sum(extract_stat_from_log('def_rtg', team_stats_games))/index
    off_rtg_recent = sum(extract_stat_from_log('off_rtg', team_stats_games[index-8:index]))/8
    def_rtg_recent = sum(extract_stat_from_log('def_rtg', team_stats_games[index-8:index]))/8

    team_stats_features = [off_rtg_totals, off_rtg_recent, def_rtg_totals, def_rtg_recent]
    feature_vector += team_stats_features


    opponent_stats_games = []
    opp_games = s2022.teams[opponent].games
    opponent_game_no = int(opponent_game_no)
    for i in range(opponent_game_no-1):
        current = opp_games[i]
        if current.home_team == opponent:
            opponent_stats_games.append(current.home_team_stats)
        elif current.away_team == opponent:
            opponent_stats_games.append(current.away_team_stats)
        else:
            return ("error", "issue with gathering team stats")
        
    opp_off_rtg_totals = sum(extract_stat_from_log('off_rtg', opponent_stats_games))/(opponent_game_no-1)
    opp_def_rtg_totals = sum(extract_stat_from_log('def_rtg', opponent_stats_games))/(opponent_game_no-1)
    opp_off_rtg_recent = sum(extract_stat_from_log('off_rtg', opponent_stats_games[index-8:index]))/(opponent_game_no-1)
    opp_def_rtg_recent = sum(extract_stat_from_log('def_rtg', opponent_stats_games[index-8:index]))/(opponent_game_no-1)

    opp_stats_features = [opp_off_rtg_totals, opp_off_rtg_recent, opp_def_rtg_totals, opp_def_rtg_recent]
    feature_vector += opp_stats_features

    label = float(player.gamelog[index]['pts'])
    if (label > 40.0):
        label = 40.0
    feature_vector.append(label)
    
    return ("success",feature_vector)


# Below code is for creating feature vectors according to svm specification, for 2022 season TODO: reorganize

# prop_player_ids = {}
# for player_id in players:
#     if "2022" not in player_id:
#         continue
#     prop_player_id = player_id[:-3].lower().replace(".", "").replace("\'", "")

#     if prop_player_id in prop_player_ids:
#         list = prop_player_ids[prop_player_id]
#         list.append(player_id)
#         prop_player_ids.update({prop_player_id: list})
#     else:
#         prop_player_ids[prop_player_id] = [player_id]

# hardcoded_propname_to_bbrefname = {
#     'karlanthony-towns2022': 'karl-anthonytowns2022',
#     'nahshonhyland2022': 'boneshyland2022',
#     'cameronthomas2022': 'camthomas2022',
#     'mohamedbamba2022': 'mobamba2022',
#     'louiswilliams2022': 'louwilliams2022',
#     'nicolasclaxton2022': 'nicclaxton2022'
# }
# unknowns = set([])
# datestring = ""
# num_found = 0
# num_not = 0
# points_prop_lines = open("points_prop_lines.txt", "r")
# for line in points_prop_lines:
#   if "Date:" in line:
#       datestring = line.split()[1]
#       continue
#   elif "Player" in line:
#       player_name = json.loads(line)["Player"]
#       if "2022" not in player_name:
#           continue
#       if player_name in hardcoded_propname_to_bbrefname:
#           player_name = hardcoded_propname_to_bbrefname[player_name]
#       if player_name in prop_player_ids:
#         prop_player_id = player_name
#       elif player_name.replace("-", "") in prop_player_ids:
#         prop_player_id = player_name.replace("-", "")
#       elif player_name[:-6]+"2022" in prop_player_ids:
#         prop_player_id = player_name[:-6]+"2022"
#       elif player_name[:-4]+"jr"+"2022" in prop_player_ids:
#         prop_player_id = player_name[:-4]+"jr"+"2022"
#       elif player_name[:-4]+"sr"+"2022" in prop_player_ids:
#         prop_player_id = player_name[:-4]+"sr"+"2022"
#       elif player_name[:-4]+"ii"+"2022" in prop_player_ids:
#         prop_player_id = player_name[:-4]+"ii"+"2022"
#       elif player_name[:-4]+"iii"+"2022" in prop_player_ids:
#         prop_player_id = player_name[:-4]+"iii"+"2022"
#       else:
#         unknowns.add(player_name)
#         continue
#       player_ids = prop_player_ids[prop_player_id]
#       found = False
#       val = ""
#       for player_id in player_ids:
#           (code, value) = featurize_instance(player_id, datestring)
#           if (code == "success"):
#               found = True
#               num_found += 1
#               break
#           else:
#               val = value
#       if (found == False):
#           num_not += 1
#           continue
#       label = value.pop(-1)
#       json_obj = json.loads(line)
#       json_obj['date'] = datestring
#       json_obj['feature_vector'] = value
#       json_obj['label'] = label
#       f = open("svm_feature_vectors.txt", "a")
#       f.write(json.dumps(json_obj) + "\n")
#       f.close()
      

# # To get a season's data
# s2020 = Season(2020)
# s2020.getTeams()
# # To save objects to a file
# with open('s2020.pkl', 'wb') as outp:
#     pickle.dump(s2020, outp, pickle.HIGHEST_PROTOCOL)

# s2021 = Season(2021)
# s2021.getTeams()
# with open('s2021.pkl', 'wb') as outp:
#     pickle.dump(s2021, outp, pickle.HIGHEST_PROTOCOL)

# s2022 = Season(2022)
# s2022.getTeams()
# with open('s2022.pkl', 'wb') as outp:
#     pickle.dump(s2022, outp, pickle.HIGHEST_PROTOCOL)

# s2023 = Season(2023)
# s2023.getTeams()
# with open('s2023.pkl', 'wb') as outp:
#     pickle.dump(s2023, outp, pickle.HIGHEST_PROTOCOL)

# with open('players.pkl', 'wb') as outp:
#     pickle.dump(player_identifier_to_object, outp, pickle.HIGHEST_PROTOCOL)

# To load objects from file:
# with open('s2022.pkl', 'rb') as inp:
#     s2022 = pickle.load(inp)
# with open('players.pkl', 'rb') as inp:
#     players = pickle.load(inp)

# example usage after loading:
# example: stephen curry full stat line from first game of the 2020 season
# print(players['StephenCurry2022GSW'].gamelog[0])



# # [TODO: Reorganize/make modular] Below is for collecting player priors

# hardcoded_538_names = {
#     "KevinKnox2022": "Kevin Knox II",
#     "RobertWilliams2022": "Robert Williams III",
#     "NicClaxton2022": "Nicolas Claxton",
#     "BonesHyland2022": "Nahshon Hyland",
#     "MarcusMorris2022": "Marcus Morris Sr",
#     "KlayThompson2022": "Klay Thompson",
#     "LanceStephenson2022": "Lance Stephenson"
# }

# options = webdriver.ChromeOptions()
# options.add_argument('--headless')

# driver_paths = ['/home/tkersulis/cs4701/project/chromedriver.exe', "/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome"]
# driver = webdriver.Chrome(executable_path=driver_paths[1], options=options)

# for player_id in players:
#     # TODO: run for all other years outside 2022
#     if "2022" not in player_id:
#         continue
#     if (players[player_id].most_recent_valid_season != {}):
#         continue
#     player = players.get(player_id)
#     if (player.exp == 0):
#         continue
#     player_full_name = player.name
#     if player_id[:-3] in hardcoded_538_names:
#         player_full_name = hardcoded_538_names[player_id[:-3]]
#         print(player_full_name)
#     player_name_url = unidecode("".join(player_full_name.replace(" ", "-")).replace(".", "").replace("\'", "").lower())
#     player_prior_url = "https://projects.fivethirtyeight.com/2022-nba-player-projections/" + player_name_url + "/"
#     try:
#         driver.get(player_prior_url)
#         time.sleep(1)
#         htmlSource = driver.page_source
#         soup = BeautifulSoup(htmlSource, "html.parser")
#         player_table = soup.find("div", class_="player-table")
#         player_hed = player_table.find("div", class_="player-hed")
#         bio_stats = player_hed.find("div", class_="left").find("ul", class_="stats").findAll("li")
#         for bio_stat in bio_stats:
#             if bio_stat.text == "Point Guard":
#                 position = 1
#             if bio_stat.text == "Shooting Guard":
#                 position = 2
#             if bio_stat.text == "Small Forward":
#                 position = 3
#             if bio_stat.text == "Power Forward":
#                 position = 4
#             if bio_stat.text == "Center":
#                 position = 5
#             if "years old" in bio_stat.text:
#                 age = bio_stat.text.split()[0]
#             if "Rookie" in bio_stat.text:
#                 raise Exception("rookie")
            
#         prior_map = {"pos": position, "age": age}
                
#         player_stats = player_table.find("div", class_="player-stats").findAll("table")
#         for player_stat_table in player_stats:
#             rows = player_stat_table.find("tbody").findAll("tr")
#             for row in rows:
#                 category = row.find("td", class_="first").text
#                 value = row.find("td", class_ = "last").text
#                 prior_map[category] = value

#         # players[player_id] = player
#         bbref_link = "https://www.basketball-reference.com/players/" + player.bbref_name + ".html"
#         player_bbref = BeautifulSoup(make_request(bbref_link).content, "html.parser")
#         most_recent_year = 2021
#         while (most_recent_year > 2021-3):
#             row = player_bbref.find("tr", id="per_game."+str(most_recent_year))
#             if row is None:
#                 most_recent_year -= 1
#                 continue
#             games_played_data = row.find("td", attrs={"data-stat" : "g"})
#             if games_played_data is None:
#                 break
#             if int(games_played_data.text) < 20:
#                 most_recent_year -= 1
#                 continue
#             ppg_data = row.find("td", attrs={"data-stat" : "pts_per_g"})
#             if ppg_data is None:
#                 break
#             prior_map["ppg"] = ppg_data.text
#             break

#         if "ppg" not in prior_map:
#             raise Exception("no prior ppg data for " + player_full_name)
#         player.most_recent_valid_season = prior_map
#         print(player.most_recent_valid_season)

#     except Exception as e:
#         print(player_full_name + " error: " + str(e))
#         print(traceback.format_exc())
#         continue

# with open('players.pkl', 'wb') as outp:
#     pickle.dump(players, outp, pickle.HIGHEST_PROTOCOL)
