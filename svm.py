import numpy as np
import json
from random import shuffle
from getting_bbref_season_data import Player, Game, Season, Team
import pickle
import traceback
from selenium import webdriver
from unidecode import unidecode
import requests
import time
from bs4 import BeautifulSoup
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC

def make_request(url):
    """
    Make a request to the given URL after waiting for 3 seconds to avoid hitting the rate limit.
    """
    time.sleep(3)
    return requests.get(url)

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
    
def featurize_instance(player_id, date_string, season_obj):
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
    games = season_obj.teams[player_team].games
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
    opp_games = season_obj.teams[opponent].games
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

def create_feature_vectors(season, players):
    prop_player_ids = {}
    for player_id in players:
        if season not in player_id:
            continue
        prop_player_id = player_id[:-3].lower().replace(".", "").replace("\'", "")

        if prop_player_id in prop_player_ids:
            list = prop_player_ids[prop_player_id]
            list.append(player_id)
            prop_player_ids.update({prop_player_id: list})
        else:
            prop_player_ids[prop_player_id] = [player_id]

    hardcoded_propname_to_bbrefname = {
        'karlanthony-towns2022': 'karl-anthonytowns2022',
        'nahshonhyland2022': 'boneshyland2022',
        'cameronthomas2022': 'camthomas2022',
        'mohamedbamba2022': 'mobamba2022',
        'louiswilliams2022': 'louwilliams2022',
        'nicolasclaxton2022': 'nicclaxton2022'
    }
    unknowns = set([])
    datestring = ""
    num_found = 0
    num_not = 0
    points_prop_lines = open("points_prop_lines.txt", "r")
    for line in points_prop_lines:
        if "Date:" in line:
            datestring = line.split()[1]
            continue
        elif "Player" in line:
            player_name = json.loads(line)["Player"]
            if season not in player_name:
                continue
            if player_name in hardcoded_propname_to_bbrefname:
                player_name = hardcoded_propname_to_bbrefname[player_name]
            if player_name in prop_player_ids:
                prop_player_id = player_name
            elif player_name.replace("-", "") in prop_player_ids:
                prop_player_id = player_name.replace("-", "")
            elif player_name[:-6]+season in prop_player_ids:
                prop_player_id = player_name[:-6]+season
            elif player_name[:-4]+"jr"+season in prop_player_ids:
                prop_player_id = player_name[:-4]+"jr"+season
            elif player_name[:-4]+"sr"+season in prop_player_ids:
                prop_player_id = player_name[:-4]+"sr"+season
            elif player_name[:-4]+"ii"+season in prop_player_ids:
                prop_player_id = player_name[:-4]+"ii"+season
            elif player_name[:-4]+"iii"+season in prop_player_ids:
                prop_player_id = player_name[:-4]+"iii"+season
            else:
                unknowns.add(player_name)
                continue
            player_ids = prop_player_ids[prop_player_id]
            found = False
            val = ""
            for player_id in player_ids:
                (code, value) = featurize_instance(player_id, datestring)
                if (code == "success"):
                    found = True
                    num_found += 1
                    break
                else:
                    val = value
            if (found == False):
                num_not += 1
                continue
            label = value.pop(-1)
            json_obj = json.loads(line)
            json_obj['date'] = datestring
            json_obj['feature_vector'] = value
            json_obj['label'] = label
            f = open("svm_feature_vectors" + str(season) + ".txt", "a")
            f.write(json.dumps(json_obj) + "\n")
            f.close()
        print(unknowns)

def collect_player_priors(season, players):
    hardcoded_538_names = {
        "KevinKnox2022": "Kevin Knox II",
        "RobertWilliams2022": "Robert Williams III",
        "NicClaxton2022": "Nicolas Claxton",
        "BonesHyland2022": "Nahshon Hyland",
        "MarcusMorris2022": "Marcus Morris Sr",
        "KevinKnox2023": "Kevin Knox II",
        "RobertWilliams2023": "Robert Williams III",
        "NicClaxton2023": "Nicolas Claxton",
        "BonesHyland2023": "Nahshon Hyland",
        "MarcusMorris2023": "Marcus Morris Sr",
    }

    options = webdriver.ChromeOptions()
    options.add_argument('--headless')

    driver_paths = ['/home/tkersulis/cs4701/project/chromedriver.exe', "/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome"]
    driver = webdriver.Chrome(executable_path=driver_paths[1], options=options)

    for player_id in players:
        if season not in player_id:
            continue
        if (players[player_id].most_recent_valid_season != {}):
            continue
        player = players.get(player_id)
        if (player.exp == 0):
            continue
        player_full_name = player.name
        if player_id[:-3] in hardcoded_538_names:
            player_full_name = hardcoded_538_names[player_id[:-3]]
        player_name_url = unidecode("".join(player_full_name.replace(" ", "-")).replace(".", "").replace("\'", "").lower())
        player_prior_url = "https://projects.fivethirtyeight.com/" + str(season) + "-nba-player-projections/" + player_name_url + "/"
        try:
            driver.get(player_prior_url)
            time.sleep(1)
            htmlSource = driver.page_source
            soup = BeautifulSoup(htmlSource, "html.parser")
            player_table = soup.find("div", class_="player-table")
            player_hed = player_table.find("div", class_="player-hed")
            bio_stats = player_hed.find("div", class_="left").find("ul", class_="stats").findAll("li")
            for bio_stat in bio_stats:
                if bio_stat.text == "Point Guard":
                    position = 1
                if bio_stat.text == "Shooting Guard":
                    position = 2
                if bio_stat.text == "Small Forward":
                    position = 3
                if bio_stat.text == "Power Forward":
                    position = 4
                if bio_stat.text == "Center":
                    position = 5
                if "years old" in bio_stat.text:
                    age = bio_stat.text.split()[0]
                if "Rookie" in bio_stat.text:
                    raise Exception("rookie")
                
            prior_map = {"pos": position, "age": age}
                    
            player_stats = player_table.find("div", class_="player-stats").findAll("table")
            for player_stat_table in player_stats:
                rows = player_stat_table.find("tbody").findAll("tr")
                for row in rows:
                    category = row.find("td", class_="first").text
                    value = row.find("td", class_ = "last").text
                    prior_map[category] = value

            bbref_link = "https://www.basketball-reference.com/players/" + player.bbref_name + ".html"
            player_bbref = BeautifulSoup(make_request(bbref_link).content, "html.parser")
            most_recent_year = int(season)-1
            while (most_recent_year > int(season)-4):
                row = player_bbref.find("tr", id="per_game."+str(most_recent_year))
                if row is None:
                    most_recent_year -= 1
                    continue
                games_played_data = row.find("td", attrs={"data-stat" : "g"})
                if games_played_data is None:
                    break
                if int(games_played_data.text) < 20:
                    most_recent_year -= 1
                    continue
                ppg_data = row.find("td", attrs={"data-stat" : "pts_per_g"})
                if ppg_data is None:
                    break
                prior_map["ppg"] = ppg_data.text
                break

            if "ppg" not in prior_map:
                raise Exception("no prior ppg data for " + player_full_name)
            player.most_recent_valid_season = prior_map
            # print(player.most_recent_valid_season)

        except Exception as e:
            # print(player_full_name + " error: " + str(e))
            if "rookie" in str(e).lower():
                continue
            f = open("prior_errors.txt", "a")
            f.write(player_full_name + " error: " + str(e) + traceback.format_exc() + "\n")
            f.close()
            continue

    with open('players_with_priors' + str(season) + '.pkl', 'wb') as outp:
        pickle.dump(players, outp, pickle.HIGHEST_PROTOCOL)

def join_player_files(players):
    for i in range(2020, 2024):
        try:
            with open('players_with_priors' + str(i) + '.pkl', 'rb') as inp:
                players_year = pickle.load(inp)
            for player in players:
                if player not in players_year:
                    continue
                if players[player].most_recent_valid_season == {} and players_year[player].most_recent_valid_season != {}:
                    players[player].most_recent_valid_season = players_year[player].most_recent_valid_season
        except:
            continue
        # TODO
    with open('players_with_priors.pkl', 'wb') as outp:
        pickle.dump(players, outp, pickle.HIGHEST_PROTOCOL)

with open('players.pkl', 'rb') as inp:
    players = pickle.load(inp)

with open('s2022.pkl', 'rb') as inp:
    s2022 = pickle.load(inp)

collect_player_priors("2023", players)



# feature_vectors = open("svm_feature_vectors.txt", "r")
# lis = []
# for line in feature_vectors:
#     json_obj = json.loads(line)
#     lis.append(json_obj)
# shuffle(lis)
# train_list = [element['feature_vector'] for element in lis[:-50]]
# train_labels = [element['label'] for element in lis[:-50]]
# test_list = [element['feature_vector'] for element in lis[-50:]]
# test_labels = [element['label'] for element in lis[-50:]]
# train_X = np.array(train_list)
# train_Y = np.array(train_labels)
# test_X = np.array(test_list)


# clf = make_pipeline(StandardScaler(), SVC(gamma='auto'))
# clf.fit(train_X, train_Y)

# f = open("svm_predictions.txt", "a")

# for i in range(len(lis)-51, len(lis)):
#     f.write(lis[i]["Player"] + " " +  lis[i]["date"] + " " + lis[i]["lines"] + " prediction: " + str(clf.predict([lis[i]["feature_vector"]])) + " result: " + str(lis[i]['label']) + "\n")

# f.close()
