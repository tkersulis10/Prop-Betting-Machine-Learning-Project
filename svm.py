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
from sklearn.preprocessing import StandardScaler
import math
# import cvxopt

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
    
def featurize_instance(player_id, date_string, season_obj, players):
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
            if ((fga + 0.44*fta) != 0):
                true_shooting = points/(2 * (fga + 0.44*fta))
            if (fta == 0):
                ft_pct = 65.0
            else:
                ft_pct = sum(ft_list)/fta
            fg3a = sum(fg3a_list)
            if (fga != 0):
                fg3_frequency = fg3a/fga
                ft_frequency = fta/fga                

            recent_form_averages = [true_shooting, ft_pct, fg3_frequency, ft_frequency]
            feature_vector += recent_form_averages
    except Exception as e:
        print(player_id + date_string +  " error: " + str(e))
        print(traceback.format_exc())
        return ("error", "problem with recent form collection")

    this_game = games[index]

    if player_team == this_game.home_team:
        feature_vector.append(1.0)
        feature_vector.append(float(this_game.home_team_game_no))
        feature_vector.append(float(this_game.away_team_game_no))
        opponent = this_game.away_team
        opponent_game_no = this_game.away_team_game_no
    elif player_team == this_game.away_team:
        feature_vector.append(0.0)
        feature_vector.append(float(this_game.away_team_game_no))
        feature_vector.append(float(this_game.home_team_game_no))
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
    opp_off_rtg_recent = sum(extract_stat_from_log('off_rtg', opponent_stats_games[index-8:index]))/8
    opp_def_rtg_recent = sum(extract_stat_from_log('def_rtg', opponent_stats_games[index-8:index]))/8

    opp_stats_features = [opp_off_rtg_totals, opp_off_rtg_recent, opp_def_rtg_totals, opp_def_rtg_recent]
    feature_vector += opp_stats_features

    label = float(player.gamelog[index]['pts'])
    if (label > 40.0):
        label = 40.0
    feature_vector.append(label)
    feature_vector.append(unidecode(players[player_id].name))

    total_player_games = 0
    for i in range(0, len(player.gamelog)):
        if (player.gamelog[i] != "IN" and player.gamelog[i] != "DNP"):
            total_player_games += 1

    if str(season_obj.year) == "2022":
        feature_vector.append("train")
    else:
        if (total_player_games >= 30 and player_index >= total_player_games - 10):
            feature_vector.append(player.identifier)
            feature_vector.append("test")
        else:
            feature_vector.append("val")
    
    return ("success",feature_vector)


# Below code is for creating feature vectors according to svm specification, for 2022 season TODO: reorganize

def create_feature_vectors(season_obj, players):
    season = str(season_obj.year)
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
        'nicolasclaxton2022': 'nicclaxton2022',
        'karlanthony-towns2023': 'karl-anthonytowns2023',
        'nahshonhyland2023': 'boneshyland2023',
        'nicolasclaxton2023': 'nicclaxton2023',
        'mohamedbamba2023': 'mobamba2023',
        'cameronthomas2023': 'camthomas2023',
    }
    unknowns = set([])
    tests = set([])
    datestring = ""
    num_found = 0
    num_not = 0
    points_prop_lines = open("points_prop_lines_raw.txt", "r")
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
                try:
                    (code, value) = featurize_instance(player_id, datestring, season_obj, players)
                    if (code == "success"):
                        found = True
                        num_found += 1
                        break
                    else:
                        val = value
                except:
                    val = "unknown error in featurizing instance"
            if (found == False):
                num_not += 1
                continue
            data_split = value.pop(-1)
            if data_split == "test":
                player_identifier = value.pop(-1)
                tests.add(player_identifier)
            player_real_name = value.pop(-1)
            label = value.pop(-1)
            json_obj = json.loads(line)
            json_obj['Player'] = player_real_name
            json_obj['date'] = datestring
            json_obj['feature_vector'] = value
            json_obj['label'] = label
            file_to_write = "svm_" + data_split + ".txt"
            f = open(file_to_write, "a")
            f.write(json.dumps(json_obj) + "\n")
            f.close()
            # f = open("svm_feature_vectors" + str(season) + ".txt", "a")
            # f.write(json.dumps(json_obj) + "\n")
            # f.close()
    with open('svm_test_players.pkl', 'wb') as outp:
        pickle.dump(tests, outp, pickle.HIGHEST_PROTOCOL)
    print(unknowns)
    print(num_found)

def collect_player_priors(season, players):
    hardcoded_538_names = {
        "NicClaxton2021": "Nicolas Claxton",
        "RobertWilliams2021": "Robert Williams III",
        "KevinKnox2022": "Kevin Knox II",
        "RobertWilliams2022": "Robert Williams III",
        "NicClaxton2022": "Nicolas Claxton",
        "BonesHyland2022": "Nahshon Hyland",
        "MarcusMorris2022": "Marcus Morris Sr",
        "KevinKnox2023": "Kevin Knox II",
        "RobertWilliams2023": "Robert Williams III",
        "MarcusMorris2023": "Marcus Morris Sr",
        "XavierTillmanSr.2023": "Xavier Tillman"
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
        print(player_id)
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
            f = open("prior_errors" + str(season) + ".txt", "a")
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
    with open('players_with_priors.pkl', 'wb') as outp:
        pickle.dump(players, outp, pickle.HIGHEST_PROTOCOL)

def evaluate(predictions, val_labels):
    tp = 0.0
    fp = 0.0
    tn = 0.0
    fn = 0.0
    pos_pred = 0
    neg_pred = 0
    for i in range(len(predictions)):
        if predictions[i] == 1.0:
            pos_pred += 1
            if val_labels[i] == 1.0:
                # print("tp")
                tp += 1
            else:
                fp += 1
        else:
            neg_pred += 1
            if val_labels[i] == -1.0:
                tn += 1
            else:
                fn += 1
    print(pos_pred)
    if (tp+fp == 0):
        over_prec = 0
    else:
        over_prec = tp/(tp+fp)
    over_recall = tp/(tp+fn)
    try:
        over_f1 = 2*(over_prec*over_recall)/(over_recall+over_prec)
    except:
        over_f1 = 0
    print(over_f1)
    if (tn+fn == 0):
        under_prec = 0
    else:
        under_prec = tn/(tn+fn)
    print(neg_pred)
    under_recall = tn/(tn+fp)
    try:
        under_f1 = 2*(under_prec*under_recall)/(under_recall+under_prec)
    except:
        under_f1 = 0
    print(under_f1)
    score = math.sqrt(over_f1*under_f1)
    return score

class SVM:
    def __init__(self, line, C, gamma, train_file):
        self.line = float(line) + 0.5
        self.C = float(C)
        self.gamma = float(gamma)
        self.b = 0
        self.X = []
        self.Y = []
        feature_vectors = open(train_file, "r")
        lis = []
        for line in feature_vectors:
            json_obj = json.loads(line)
            lis.append(json_obj)
        train_list = [element['feature_vector'] for element in lis]
        scaler = StandardScaler()
        scaler.fit(train_list)
        self.scaler = scaler
        self.X = np.array(scaler.transform(train_list))
        train_labels = [element['label'] for element in lis]
        train_labels = [1.0 if x > self.line else -1.0 for x in train_labels]
        self.Y = np.array(train_labels)

    def rbf_kernel(self, xi, xj):
        l2_norm = np.linalg.norm(xi - xj)**2
        return np.exp(-self.gamma * l2_norm)
    
    def train_from_scratch(self):
        dataset_size = len(self.X)
        kernel_matrix = np.zeros((dataset_size, dataset_size))
        for i in range(dataset_size):
            for j in range(dataset_size):
                if j < i:
                    kernel_matrix[i][j] = kernel_matrix[j][i]
                else:
                    kernel_matrix[i][j] = self.rbf_kernel(self.X[i], self.X[j])
        
        # Note: cvxopt was not working on my computer, I wrote and ran the following in colab notebooks
        # formulate dual form of soft margin SVM as a quadratic programming problem, solve using cvxopt
        # cvxopt has parameters P, q, G, h, A, b. See cvxopt qp documentation to see which variable represents what

        P = np.zeros((dataset_size, dataset_size))
        for i in range(dataset_size):
            for j in range(dataset_size):
                P[i][j] = kernel_matrix*self.Y[i]*self.Y[j]
        
        q = np.ones((dataset_size, 1))*-1

        negative_alphas = np.identity((dataset_size, dataset_size))*-1
        positive_alphas = np.identity((dataset_size, dataset_size))
        G = np.row_stack((negative_alphas, positive_alphas))

        min_alphas = np.zeros(dataset_size)
        max_alphas = np.ones(dataset_size)*self.C
        h = np.hstack(min_alphas, max_alphas)

        A = self.Y.reshape(1, -1)
        b = np.zeros(1)

        P = cvxopt.matrix(P)
        q = cvxopt.matrix(q)
        G = cvxopt.matrix(G)
        h = cvxopt.matrix(h)
        A = cvxopt.matrix(A)
        b = cvxopt.matrix(b)
        qp_solution = cvxopt.solvers.qp(P, q, G, h, A, b)
        self.alphas = np.array(qp_solution['x'])
        with open('./alphas/alphas_' + str(self.line)[0] + '.npy', 'wb') as f:
            np.save(f, self.alphas)

    def calculate_b(self, start_from):
        for i in range(start_from, len(self.alphas)):
            if self.support_vector_mask[i] == 1:
                index = i
                break
        b = self.Y[index]
        for i in range(len(self.support_vector_mask)):
            if self.support_vector_mask[i] == 1:
                add = self.Y[i]*self.alphas[i]*self.rbf_kernel(self.X[index], self.X[i])
                b -= add
        return (b, index)

    def train_from_alphas(self, alphas):
        self.alphas = alphas
        self.support_vector_mask = alphas > 1e-5
        count = 0
        for i in self.support_vector_mask:
            if i == 1:
                count = count + 1
        print(count)

        avg_b = 0.0
        start_ind = 0
        for i in range(10):
            (b, index) = self.calculate_b(start_ind)
            avg_b += b
            start_ind = index + 1
        avg_b = avg_b/10
        self.b = avg_b


    def predict(self, x):
        prediction = 0
        x = self.scaler.transform(np.array([x]))
        for i in range(len(self.support_vector_mask)):
            if self.support_vector_mask[i] == 1:
                prediction += self.alphas[i] * self.Y[i] * self.rbf_kernel(self.X[i], x)
        prediction += self.b
        # print(prediction[0])
        return prediction[0]
    
class fullSVM:
    def __init__(self):
        self.model_map = {}
        for i in range(38):
            print(i)
            with open('./alphas/alphas_' + str(i) + '.npy', 'rb') as f:
                alphas = np.load(f)
                c = 1.0
                svm = SVM(i, c, 0.01, "svm_train.txt")
                svm.train_from_alphas(alphas)
                self.model_map[i] = svm

    def predict(self, x):
        i = 37
        pred = 0.0
        while i >= 0:
            model = self.model_map[i]
            if model.predict(x) > 0:
                pred = i + 1
                return pred
            i -= 1
        return pred
    
def grid_search(C_list, gamma_list, model_num):
    ou_value = float(model_num) + 0.5
    bestC = 0.0
    bestg = 0.0
    best_score = 0.0
    for c in C_list:
        for g in gamma_list:
            train_feature_vectors = open("svm_train.txt", "r")
            val_feature_vectors = open("svm_val.txt", "r")
            train = []
            for line in train_feature_vectors:
                json_obj = json.loads(line)
                train.append(json_obj)
            val = []
            for line in val_feature_vectors:
                json_obj = json.loads(line)
                val.append(json_obj)
            train_points = [element['feature_vector'] for element in train]
            scaler = StandardScaler()
            scaler.fit(train_points)
            tr_list = scaler.transform(train_points)
            train_labels = [element['label'] for element in train]
            train_labels = [1.0 if x > ou_value else -1.0 for x in train_labels]
            val_points = [element['feature_vector'] for element in val]
            val_labels = [element['label'] for element in val]
            val_labels = [1.0 if x > ou_value else -1.0 for x in val_labels]
            train_X = np.array(tr_list)
            train_Y = np.array(train_labels)
            val_X = np.array(scaler.transform(val_points))

            predictions = []
            with open('./alphas/alphas_' + str(model_num) + '.npy', 'rb') as f:
                alphas = np.load(f)
                c = 1.0
                svm = SVM(model_num, c, 0.01, "svm_train.txt")
                svm.train_from_alphas(alphas)
            for x in val_X:
                predictions.append((svm.predict(x)))
            predictions = np.array([-1.0 if x < 0 else 1.0 for x in predictions])
            score = evaluate(predictions, val_labels)
            f = open("./models_gd/" + str(model_num)+"model_gd5.txt", "a")
            f.write("(" + str(c) + "," + str(g) + "), " + str(score) + "\n")
            f.close()
            print("(" + str(c) + "," + str(g) + "), " + str(score))
            if (score > best_score):
                bestC = c
                bestg = g
                best_score = score
    print("best: (" + str(bestC) + "," + str(bestg) + "), " + str(best_score))
    f = open("./models_gd/" + str(model_num)+"model_gd5.txt", "a")
    f.write("best: (" + str(bestC) + "," + str(bestg) + "), " + str(best_score))
    f.close()

# with open('players.pkl', 'rb') as inp:
#     players = pickle.load(inp)

# with open('s2023.pkl', 'rb') as inp:
#     s2023 = pickle.load(inp)

# with open('svm_test_players.pkl', 'rb') as inp:
#     test_players = pickle.load(inp)

# test_player_map = {}

# fullSVM = fullSVM()

# for player_id in test_players:
#     player = players[player_id]
#     team = player.team
#     pred_list = []
#     label_list = []
#     date_list = []
#     for i in range(len(player.gamelog)):
#         actual_date = team.games[i].date
#         bbref_datestring = team.games[i].id.split("/")[-1]
#         bbref_date = bbref_datestring[:-4]
#         year = bbref_date[:4]
#         month = int(bbref_date[4:6])
#         day = int(bbref_date[6:])
#         date_string = str(month) + "-" + str(day) + "-" + year
#         # print(date_string)
#         (code, value) = featurize_instance(player_id, date_string, s2023, players)
#         if code == "success":
#             if value.pop(-1) == "test":
#                 player_identifier = value.pop(-1)
#                 print(player_identifier)
#                 player_real_name = value.pop(-1)
#                 label = value.pop(-1)

#                 lines = "none"
#                 test_lines = open("svm_test.txt", "r")
#                 for line in test_lines:
#                     json_obj = json.loads(line)
#                     real_name = json_obj["Player"]
#                     match_date = json_obj["date"]
#                     if player_real_name == real_name and match_date == date_string:
#                         lines = json_obj["lines"]

#                 pred = fullSVM.predict(value)

#                 json_obj = json.dumps({"label": label, "pred": pred, "lines": lines, "name": unidecode(player.name), "feature_vector": value})
#                 f = open("svm_test_full.txt", "a")
#                 f.write(json_obj + "\n")
#                 f.close()

#                 pred_list.append(pred)
#                 label_list.append(label)
#                 date_list.append(actual_date)
#         else:
#             print(value)
#     list_val = ['Stat: pts', 'none', 'none', pred_list, label_list, date_list]
#     test_player_map[player.name] = list_val

# with open('svm_test_map_points.pkl', 'wb') as outp:
#     pickle.dump(test_player_map, outp, pickle.HIGHEST_PROTOCOL) 

# create_feature_vectors(s2023, players)

# with open('./alphas/alphas_6.npy', 'rb') as f:
#     alphas_6 = np.load(f)
#     svm_6 = SVM(6, 10.0, 0.01, "svm_train.txt")
#     svm_6.train_from_alphas(alphas_6)
#     x = np.array([0.0, 0.0, 0.0, 1.0, 0.0, 5.0, 31.0, 82.0, 240.0, 100.0, 59.0, 78.0, 12.0, 71.0, 17.0, 7.0, 10.0, 12.0, 3.1, 0.8, 1.6, 7.0, 12, 0.5152807391613362, 0.75, 0.6274509803921569, 0.23529411764705882, 4.833333333333333, 4.25, 25.333333333333332, 2.0, 2.0, 4.0, 7.0, 9.0, 3.0, 4.0, 5.0, 5.0, 6.0, 5.8, 9.9, 11.3, 12.8, 13.3, 23.0, 25.0, 26.0, 28.0, 32.0, 4.0, 5.0, 9.9, 23.0, 0.4, 65.0, 0.0, 0.0, 2.0, 4.0, 5.0, 6.0, 9.9, 12.9, 20.0, 23.0, 0.2727272727272727, 65.0, 0.0, 0.0, 2.0, 4.0, 5.0, 8.0, 3.0, 5.0, 6.0, 6.0, 4.7, 8.9, 9.9, 12.9, 20.0, 23.0, 29.0, 33.0, 0.475, 65.0, 0.15, 0.0, 0.0, 2.0, 2.0, 2.0, 2.0, 4.0, 5.0, 8.0, 0.0, 3.0, 3.0, 4.0, 5.0, 6.0, 6.0, 8.0, 0.0, 4.7, 5.8, 8.9, 9.9, 12.9, 13.3, 18.8, 16.0, 20.0, 23.0, 24.0, 25.0, 28.0, 29.0, 33.0, 0.35714285714285715, 65.0, 0.08571428571428572, 0.0, 1.0, 13.0, 15.0, 115.25833333333333, 110.98749999999998, 111.8, 110.89999999999999, 107.14999999999999, 109.1625, 109.3142857142857, 109.98749999999998])
#     print(svm_6.predict(x))


# c_list = [0.1, 1, 10]
# g_list = [1e-5, 1e-4, 1e-3, 0.01, 0.1]

# grid_search(c_list, g_list, 15)


# val_feature_vectors = open("svm_val.txt", "r")
# label_counts = {}
# line_counts = {}
# for line in val_feature_vectors:
#     json_obj = json.loads(line)
#     lab = json_obj["label"]
#     label_counts[lab] = label_counts.get(lab, 0) + 1
#     lines = json.loads(json_obj["lines"])
#     k = float(lines["consensus"][0].split("@")[0])
#     line_counts[k] = line_counts.get(k, 0) + 1
# # print(label_counts)
# # print(line_counts)

# c_list = [1, 3, 5, 10, 100]
# g_list = [0.01]
# i = 37
# while i>15:
#     ou = float(str(i) + ".5")
#     print()
#     print("training for " + str(ou))
#     tot_u = 0
#     tot_o = 0
#     for lab in label_counts:
#         if lab < ou:
#             tot_u += label_counts[lab]
#         else:
#             tot_o += label_counts[lab]
#     print(str(tot_o) + ", " + str(tot_u))
#     tot_u = 0.0
#     tot_o = 0.0
#     for line in line_counts:
#         if line < ou:
#             tot_u += line_counts[line]
#         elif line > ou:
#             tot_o += line_counts[line]
#     tot_u += line_counts.get(ou, 0)/2
#     tot_o += line_counts.get(ou, 0)/2
#     print(str(tot_o) + ", " + str(tot_u))
#     grid_search(c_list, g_list, i)
#     i -= 1




# with open('players.pkl', 'rb') as inp:
#     players = pickle.load(inp)

# with open('s2023.pkl', 'rb') as inp:
#     s2023 = pickle.load(inp)

# create_feature_vectors(s2023, players)
