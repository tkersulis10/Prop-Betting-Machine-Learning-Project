import pickle
import random
from getting_bbref_season_data import Player
from getting_bbref_season_data import Season
from getting_bbref_season_data import Team
from getting_bbref_season_data import Game

def train_players(player_list, alpha_divider):
    """
    Train players in player_list.
    """
    player_feature_dict = {}
    for player_var in player_list:
        # Get player details
        player = player_var.gamelog
        player_name = player_var.name
        team_name = player_var.team.name
        team_games = player_var.team.games
        team_roster = []
        for team_member in player_var.team.players:
            team_roster.append(team_member.bbref_name)
        roster_size = len(team_roster)
        
        # Get feature values from each individual game in the season
        actual_points = []
        feature_values = []
        num_games = 0
        for i in range(82):
            if type(player[i]) != str:
                # Get team's and opponents stats and inactives
                if team_games[i].home_team == team_name:
                    home = True
                else:
                    home = False
                if home == True:
                    opp_team_stats = team_games[i].away_team_stats
                    team_inactives = team_games[i].home_inactives # GSW own inactives
                else:
                    opp_team_stats = team_games[i].home_team_stats
                    team_inactives = team_games[i].away_inactives # GSW own inactives

                # Extract player's gamelog stats as features
                feature_values_strings = list(player[i].values())
                actual_points.append(int(feature_values_strings.pop(18)))
                feature_values.append([])
                num_games += 1

                # Convert stats to valid floats
                for value in feature_values_strings:
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
                    feature_values[num_games - 1].append(float(value))
                
                # Extract player's team inactives for each game as features
                inactives_features = [0] * roster_size
                for team_member in range(roster_size):
                    if team_roster[team_member] in team_inactives:
                        inactives_features[team_member] = 1 # set to 1 if player inactive

                # Extract opposing team's game-by-game stats as features
                opp_team_stat_list = list(opp_team_stats.values())
                opp_team_features = [0] * 35
                for game_num in range(len(opp_team_stat_list)):
                    # Convert stats to valid floats
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

                # Add all features to one list
                feature_values[num_games - 1] += opp_team_features
                feature_values[num_games - 1] += inactives_features
        
        # Initialize weights
        num_features= len(feature_values[0])
        weights = [0] * num_features

        # Initialize hyperparameters
        alpha = 1 / (num_games * num_features * alpha_divider) # learning rate

        # Train weights on first (num_games - 10) games of the player's season
        for game in range(num_games - 10):
            prediction = 0
            for feature in range(num_features):
                prediction += feature_values[game][feature] * weights[feature]
            difference = actual_points[game] - prediction
            for weight in range(num_features):
                weights[weight] += alpha * difference * feature_values[game][weight]

        player_feature_dict[player_name] = (feature_values, weights, actual_points)
    
    # Return dictionary of each player's features, weights, and actual points
    return player_feature_dict

def evaluate_players(player_feature_dict, start_games_from_end, end_games_from_end):
    """
    Evaluates the predicted points scored for each player in player_feature_dict
    versus their actual points scored from (including) start_games_from_end
    from the end to (excluding) end_games_from_end from the end.

    Example: If player played 70 games in the season and you want to evaluate
    the player's last 10 games (indexes 60 - 69), start_games_from_end = 10
    and end_games_from_end = 0.
    """
    results = {}
    for player in player_feature_dict.keys():
        # Initialize needed variables
        num_games = len(player_feature_dict[player][0])
        feature_values = player_feature_dict[player][0]
        weights = player_feature_dict[player][1]
        actual_points = player_feature_dict[player][2]
        num_features = len(feature_values[0])
        num_evaluation_games = start_games_from_end - end_games_from_end
        start_game = num_games - start_games_from_end
        end_game = num_games - end_games_from_end

        # Get prediction for points for each of the specified games
        final_prediction = [0] * num_evaluation_games
        count = 0
        for game in range(start_game, end_game):
            for feature in range(num_features):
                final_prediction[count] += feature_values[game][feature] * weights[feature]
            count += 1

        # Compute the predicted vs average points and add to result dict
        predicted = sum(final_prediction) / num_evaluation_games
        actual = sum(actual_points[start_game: end_game]) / num_evaluation_games
        results[player] = (predicted, actual)

    return results

def validation(player_list, random_tests):
    """
    Randomly test different learning rates and initial weights to find and
    return the best performing hyperparameters based on least squares on
    player_list. Tests each hyperparameter on random_tests number of random
    values.
    """
    # Generate random number for the divider of alpha (learning rate)
    random_dividers = []
    for i in range(random_tests):
        random_dividers.append(random.randint(1, 500))

    # Find the most accurate divider
    best_divider = 1
    best_divider_lss = float('inf')
    for divider in random_dividers:
        # Train model using divider
        player_feature_dict = train_players(player_list, divider)

        # Evaluate model using divider
        results = evaluate_players(player_feature_dict, 10, 5)

        # Check if this divider is the best one so far using least squares sum
        ls_sum = 0
        for player in results.keys():
            ls_sum += abs(results[player][0] - results[player][1]) ** 2
        
        if ls_sum < best_divider_lss:
            best_divider = divider
            best_divider_lss = ls_sum
    
    return best_divider

def test_players(player_feature_dict):
    """
    Test features and weights in player_feature_dict for each player.
    Tests on each player's last 5 games of the season and outputs
    the model's predicted points vs player's actual points for the last 5
    games of the player's season.
    """
    results = evaluate_players(player_feature_dict, 5, 0)

    for player in results.keys():
        # Output the predicted vs average points and write to file
        output_string1 = player + " average predicted points: " + str(results[player][0])
        output_string2 = player + " actual average points: " + str(results[player][1])
        with open("reinforcement_learning_output.txt", "a") as file:
            file.write(output_string1 + "\n")
            file.write(output_string2 + "\n")

with open('s2022.pkl', 'rb') as inp:
    s2022 = pickle.load(inp)
with open('players.pkl', 'rb') as inp:
    players = pickle.load(inp)

gamelog_list = []
gamelog_list.append(players['StephenCurry2022GSW'])
gamelog_list.append(players['AndrewWiggins2022GSW'])
gamelog_list.append(players['JordanPoole2022GSW'])
gamelog_list.append(players['KlayThompson2022GSW'])
gamelog_list.append(players['DraymondGreen2022GSW'])
gamelog_list.append(players['OttoPorterJr.2022GSW'])
gamelog_list.append(players['KevonLooney2022GSW'])
gamelog_list.append(players['DamionLee2022GSW'])
gamelog_list.append(players['AndreIguodala2022GSW'])
gamelog_list.append(players['GaryPaytonII2022GSW'])
gamelog_list.append(players['JonathanKuminga2022GSW'])
gamelog_list.append(players['NemanjaBjelica2022GSW'])
gamelog_list.append(players['JuanToscano-Anderson2022GSW'])
gamelog_list.append(players['MosesMoody2022GSW'])
gamelog_list.append(players['ChrisChiozza2022GSW'])

# Too few games played
# gamelog_list.append(players['JeffDowtin2022GSW'])
# gamelog_list.append(players['QuinndaryWeatherspoon2022GSW'])

# Find best alpha divider hyperparameter
best_alpha = validation(gamelog_list, 20)
with open("reinforcement_learning_output.txt", "a") as file:
    file.write("Best divider found: " + str(best_alpha) + "\n")

# Train model using best hyperparameter
player_dict = train_players(gamelog_list, best_alpha)

# Evaluate model
test_players(player_dict)