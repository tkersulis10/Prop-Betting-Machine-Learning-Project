import pickle
from getting_bbref_season_data import Player
from getting_bbref_season_data import Season
from getting_bbref_season_data import Team
from getting_bbref_season_data import Game

with open('s2020.pkl', 'rb') as inp:
    s2020 = pickle.load(inp)
with open('players.pkl', 'rb') as inp:
    players = pickle.load(inp)

gamelog_list = []
gamelog_list.append((players['StephenCurry2022GSW'], "Stephen Curry"))
gamelog_list.append((players['AndrewWiggins2022GSW'], "Andrew Wiggins"))
gamelog_list.append((players['JordanPoole2022GSW'], "Jordan Poole"))
gamelog_list.append((players['KlayThompson2022GSW'], "Klay Thompson"))
gamelog_list.append((players['DraymondGreen2022GSW'], "Draymond Green"))
gamelog_list.append((players['OttoPorterJr.2022GSW'], "Otto Porter Jr."))
gamelog_list.append((players['KevonLooney2022GSW'], "Kevon Looney"))
gamelog_list.append((players['DamionLee2022GSW'], "Damion Lee"))
gamelog_list.append((players['AndreIguodala2022GSW'], "Andre Iguodala"))
gamelog_list.append((players['GaryPaytonII2022GSW'], "Gary Payton II"))
gamelog_list.append((players['JonathanKuminga2022GSW'], "Jonathan Kuminga"))
gamelog_list.append((players['NemanjaBjelica2022GSW'], "Nemanja Bjelica"))
gamelog_list.append((players['JuanToscano-Anderson2022GSW'], "Juan Toscano-Anderson"))
gamelog_list.append((players['MosesMoody2022GSW'], "Moses Moody"))
gamelog_list.append((players['ChrisChiozza2022GSW'], "Chris Chiozza"))
gamelog_list.append((players['JeffDowtin2022GSW'], "Jeff Dowtin"))
gamelog_list.append((players['QuinndaryWeatherspoon2022GSW'], "Quinndary Weathersoon"))
# with open("stephencurry2022gamelog.txt", "a") as file:
#   file.write("Stephen Curry 2020 Gamelog:\n")
#   counter = 1
#   for game in gamelog_list:
#     file.write(str(counter) + ": ")
#     file.write(str(game))
#     file.write("\n")
#     counter += 1

for player_var, name in gamelog_list:
    player = player_var.gamelog
    team_games = player_var.team.games
    game_count = 0
    while type(player[game_count]) == str:
        game_count += 1
    features = list(player[game_count].keys())
    features.pop(18)
    actual_points = []
    feature_values_floats = []
    for i in range(82):
        if type(player[i]) != str:
            feature_values = list(player[i].values())
            # print(len(feature_values))
            actual_points.append(int(feature_values.pop(18)))
            # feature_values[0] = int(feature_values[0][0:2]) + (int(feature_values[0][3:5]) / 60)
            if team_games[i].home_team == "GSW":
                home = True
            else:
                home = False
            if home == True:
                team_stats = team_games[i].away_team_stats
            else:
                team_stats = team_games[i].home_team_stats
            opp_team_stat_list = list(team_stats.values())
            opp_team_features = [0] * 35
            for game_num in range(len(opp_team_stat_list)):
                opp_value = opp_team_stat_list[game_num]
                time = opp_value.find(":")
                decimal = opp_value.find(".")
                plus = opp_value.find("+")
                if opp_value == "":
                    opp_value = 0
                if time >= 0:
                    opp_value = int(opp_value[0:time]) + (int(opp_value[time + 1:5]) / 60)
                if decimal == 0:
                    opp_value = "0" + opp_value
                if plus == 0:
                    opp_value = opp_value[1:]
                opp_team_features[game_num] = float(opp_value)
            feature_values_floats.append([])
            games_so_far = len(feature_values_floats)
            for value in feature_values:
                time = value.find(":")
                decimal = value.find(".")
                plus = value.find("+")
                if value == "":
                    value = 0
                if time >= 0:
                    value = int(value[0:time]) + (int(value[time + 1:5]) / 60)
                if decimal == 0:
                    value = "0" + value
                if plus == 0:
                    value = value[1:]
                feature_values_floats[games_so_far - 1].append(float(value))
            feature_values_floats[games_so_far - 1] += opp_team_features
            # print(feature_values_floats[games_so_far - 1])
    num_features= len(feature_values_floats[0])
    weights = [0] * num_features
    #initial_prediction = 0
    #for i in range(num_features):
    #    initial_prediction += feature_values_floats[0][i]
    #print(feature_values_floats)
    #print(initial_prediction)
    # print(actual_points)
    num_games = len(feature_values_floats)
    alpha = 1 / (num_games * num_features * 100) # hyperparameter
    for game in range(num_games - 5):
        prediction = 0
        for feature in range(num_features):
            prediction += feature_values_floats[game][feature] * weights[feature]
        difference = actual_points[game] - prediction
        # print("difference: " + str(difference))
        for weight in range(num_features):
            weights[weight] += alpha * difference * feature_values_floats[game][weight]
        # print("weights: " + str(weights[0]))
    # print(weights)
    final_prediction = [0] * 5
    count = 0
    for game in range(num_games - 5, num_games):
        for feature in range(num_features):
            final_prediction[count] += feature_values_floats[game][feature] * weights[feature]
        count += 1
    output_string1 = name + " average predicted points: " + str(sum(final_prediction) / len(final_prediction))
    # print(output_string1)
    output_string2 = name + " actual average points: " + str(sum(actual_points[num_games - 5:]) / 5)
    # print(output_string2)
    with open("reinforcement_learning_output.txt", "a") as file:
        file.write(output_string1 + "\n")
        file.write(output_string2 + "\n")
    # print(num_games)