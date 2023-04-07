import pickle
import random
import math
from getting_bbref_season_data import Player
from getting_bbref_season_data import Season
from getting_bbref_season_data import Team
from getting_bbref_season_data import Game

def convert_to_valid_value(value):
    """
    Convert the value from an invalid string to a valid float.
    """
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
    return float(value)

def train_players(player_list, player_alpha_divider):
    """
    Trains and returns trained players in player_list. Only returns players
    that played at least 20 games this season.
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
                    new_value = convert_to_valid_value(value)
                    feature_values[num_games - 1].append(new_value)
                
                # Extract player's team inactives for each game as features
                inactives_features = [0] * roster_size
                for team_member in range(roster_size):
                    if team_roster[team_member] in team_inactives:
                        inactives_features[team_member] = 1 # set to 1 if player inactive

                # Extract opposing team's game-by-game stats as features
                opp_team_stat_list = list(opp_team_stats.values())
                opp_team_features = []
                for opp_value in opp_team_stat_list:
                    # Convert stats to valid floats
                    new_opp_value = convert_to_valid_value(opp_value)
                    opp_team_features.append(new_opp_value)

                # Add all features to one list
                feature_values[num_games - 1] += opp_team_features
                feature_values[num_games - 1] += inactives_features
        
        # Only train if player played at least 20 games
        if num_games >= 20:
            # Initialize weights
            num_features= len(feature_values[0])
            weights = [0] * num_features

            # Initialize hyperparameters
            player_alpha = 1 / (num_games * num_features * player_alpha_divider) # learning rate

            # Train weights on first (num_games - 10) games of the player's season
            for game in range(num_games - 10):
                prediction = 0
                for feature in range(num_features):
                    prediction += feature_values[game][feature] * weights[feature]
                difference = actual_points[game] - prediction
                for weight in range(num_features):
                    weights[weight] += player_alpha * difference * feature_values[game][weight]

            player_feature_dict[player_name] = (feature_values, weights, actual_points)
    
    # Return dictionary of each player's features, weights, and actual points
    return player_feature_dict

def evaluate_players(player_feature_dict, start_games_from_end, end_games_from_end, step):
    """
    Evaluates the predicted points scored for each player in player_feature_dict
    versus their actual points scored from (including) start_games_from_end
    from the end to (excluding) end_games_from_end from the end by using every
    step game.

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
        num_evaluation_games = math.ceil((start_games_from_end - end_games_from_end) / 2)
        print(num_evaluation_games)
        start_game = num_games - start_games_from_end
        end_game = num_games - end_games_from_end

        # Get prediction for points for each of the specified games
        final_prediction = [0] * num_evaluation_games
        real_points = []
        count = 0
        for game in range(start_game, end_game, step):
            for feature in range(num_features):
                final_prediction[count] += feature_values[game][feature] * weights[feature]
            real_points.append(actual_points[game])
            count += 1

        # Compute the predicted vs average points and add to result dict
        predicted = sum(final_prediction) / num_evaluation_games
        actual = sum(real_points) / num_evaluation_games
        results[player] = (predicted, actual)

    return results

def validation(player_list, random_tests):
    """
    Randomly test different learning rates and initial weights to find and
    return the best performing hyperparameters based on least squares on
    player_list. Tests each hyperparameter on random_tests number of random
    values. Validates on each players 10th, 8th, 6th, 4th, and 2nd last games
    of the season.
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
        results = evaluate_players(player_feature_dict, 10, 0, 2)

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
    Tests on each player's 9th, 7th, 5th, 3rd and last games of the season
    and outputs the model's predicted points vs player's actual points for
    these games of the player's season.
    """
    results = evaluate_players(player_feature_dict, 9, 0, 2)

    for player in results.keys():
        # Output the predicted vs average points and write to file
        output_string1 = player + " average predicted points: " + str(results[player][0])
        output_string2 = player + " actual average points: " + str(results[player][1])
        with open("reinforcement_learning_output.txt", "a") as file:
            file.write(output_string1 + "\n")
            file.write(output_string2 + "\n")

def get_opp_team_stats(team, learning_rate):
    """
    Gets the stats for an opposing team throughout the season. Uses learning_rate
    to place more emphasis on recent games. The higher the learning rate, the
    higher the emphasis on recent games.
    """
    team_games = team.games
    team_name = team.name
    average_stats = [0] * 35
    for game in range(len(team_games)):
        if team_games[game].home_team == team_name:
            home = True
        else:
            home = False
        if home == True:
            team_stats = team_games[game].home_team_stats
            team_inactives = team_games[game].home_inactives # team inactives
        else:
            team_stats = team_games[game].away_team_stats
            team_inactives = team_games[game].away_inactives

        team_stat_list = list(team_stats.values())
        team_features = []
        for value in team_stat_list:
            # Convert stats to valid floats
            new_value = convert_to_valid_value(value)
            team_features.append(new_value)

        alpha = learning_rate
        for feature in range(len(team_features)):
            average_stats[feature] += (alpha * team_features[feature]) - (alpha * average_stats[feature])
    
    return average_stats
        

with open('s2022.pkl', 'rb') as inp:
    s2022 = pickle.load(inp)
with open('players.pkl', 'rb') as inp:
    players = pickle.load(inp)

# Find the predicted stats for every player in the season
gamelog_list = []
team_list = []
for player in players:
   player_var = players[player]
   if player_var.year == 2022:
       gamelog_list.append(player_var)

       # Add all teams to team_list
       player_team = player_var.team
       if player_team not in team_list:
           team_list.append(player_team)

team_stats = {}
for team in team_list:
    team_stats[team.name] = get_opp_team_stats(team, 0.0005)

# Find best alpha divider hyperparameter
best_alpha = validation(gamelog_list, 20)
with open("reinforcement_learning_output.txt", "a") as file:
    file.write("Best divider found: " + str(best_alpha) + "\n")

# Train model using best hyperparameter
player_dict = train_players(gamelog_list, best_alpha)

# Evaluate model
test_players(player_dict)