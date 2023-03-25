import pickle
import getting_bbref_season_data

#with open('s2020.pkl', 'rb') as inp:
#    s2020 = pickle.load(inp)
with open('players.pkl', 'rb') as inp:
    players = pickle.load(inp)

gamelog_list = []
gamelog_list.append((players['StephenCurry2022GSW'].gamelog, "Stephen Curry"))
gamelog_list.append((players['AndrewWiggins2022GSW'].gamelog, "Andrew Wiggins"))
gamelog_list.append((players['JordanPoole2022GSW'].gamelog, "Jordan Poole"))
gamelog_list.append((players['KlayThompson2022GSW'].gamelog, "Klay Thompson"))
gamelog_list.append((players['DraymondGreen2022GSW'].gamelog, "Draymond Green"))
gamelog_list.append((players['OttoPorterJr.2022GSW'].gamelog, "Otto Porter Jr."))
gamelog_list.append((players['KevonLooney2022GSW'].gamelog, "Kevon Looney"))
gamelog_list.append((players['DamionLee2022GSW'].gamelog, "Damion Lee"))
gamelog_list.append((players['AndreIguodala2022GSW'].gamelog, "Andre Iguodala"))
gamelog_list.append((players['GaryPaytonII2022GSW'].gamelog, "Gary Payton II"))
gamelog_list.append((players['JonathanKuminga2022GSW'].gamelog, "Jonathan Kuminga"))
gamelog_list.append((players['NemanjaBjelica2022GSW'].gamelog, "Nemanja Bjelica"))
gamelog_list.append((players['JuanToscano-Anderson2022GSW'].gamelog, "Juan Toscano-Anderson"))
gamelog_list.append((players['MosesMoody2022GSW'].gamelog, "Moses Moody"))
gamelog_list.append((players['ChrisChiozza2022GSW'].gamelog, "Chris Chiozza"))
gamelog_list.append((players['JeffDowtin2022GSW'].gamelog, "Jeff Dowtin"))
gamelog_list.append((players['QuinndaryWeatherspoon2022GSW'].gamelog, "Quinndary Weathersoon"))
# with open("stephencurry2022gamelog.txt", "a") as file:
#   file.write("Stephen Curry 2020 Gamelog:\n")
#   counter = 1
#   for game in gamelog_list:
#     file.write(str(counter) + ": ")
#     file.write(str(game))
#     file.write("\n")
#     counter += 1

for player, name in gamelog_list:
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
            feature_values_floats.append([])
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
                feature_values_floats[len(feature_values_floats) - 1].append(float(value))
    num_features= len(features)
    weights = [0] * num_features
    #initial_prediction = 0
    #for i in range(num_features):
    #    initial_prediction += feature_values_floats[0][i]
    #print(feature_values_floats)
    #print(initial_prediction)
    # print(actual_points)
    num_games = len(feature_values_floats)
    alpha = 1 / (num_games * 500) # hyperparameter
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
    output_string = name + " average predicted points: " + str(sum(final_prediction) / len(final_prediction))
    print(output_string)
    with open("reinforcement_learning_output.txt", "a") as file:
        file.write(output_string + "\n")
    # print(num_games)