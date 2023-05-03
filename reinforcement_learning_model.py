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


def train_players(stat, player_list, weight_alpha_divider, feature_alpha_divider):
    """
    Trains and returns trained players in player_list on stat. Only returns
    players that played at least 20 games this season. Uses hyperparameters
    weight_alpha_divider for the weights and feature_alpha_divider for the
    exponential rolling average of a player statistics that season.
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
        actual_stats = []
        feature_values = []
        num_games = 0
        opp_team_list = []
        for i in range(82):
            if type(player[i]) != str:
                # Get team's and opponents stats and inactives
                if team_games[i].home_team == team_name:
                    home = True
                else:
                    home = False
                if home == True:
                    opp_team = team_games[i].away_team
                    opp_team_stats = team_games[i].away_team_stats
                    # GSW own inactives
                    team_inactives = team_games[i].home_inactives
                else:
                    opp_team = team_games[i].home_team
                    opp_team_stats = team_games[i].home_team_stats
                    # GSW own inactives
                    team_inactives = team_games[i].away_inactives
                opp_team_list.append(opp_team)

                # Extract player's gamelog stats as features
                feature_values_strings = list(player[i].values())
                actual_stats.append(int(feature_values_strings.pop(stat)))
                feature_values.append([])
                num_games += 1

                # Convert stats to valid floats
                for value in feature_values_strings:
                    new_value = convert_to_valid_value(value)
                    feature_values[num_games - 1].append(new_value)

                # Extract opposing team's game-by-game stats as features
                opp_team_stat_list = list(opp_team_stats.values())
                opp_team_features = []
                for opp_value in opp_team_stat_list:
                    # Convert stats to valid floats
                    new_opp_value = convert_to_valid_value(opp_value)
                    opp_team_features.append(new_opp_value)

                # Extract player's team inactives for each game as features
                inactives_features = [0] * roster_size
                for team_member in range(roster_size):
                    if team_roster[team_member] in team_inactives:
                        # set to 1 if player inactive
                        inactives_features[team_member] = 1

                # Add all features to one list
                feature_values[num_games - 1] += opp_team_features
                feature_values[num_games - 1] += inactives_features

        # Only train if player played at least 20 games
        if num_games >= 20:
            # Initialize weights
            num_features = len(feature_values[0])
            weights = [0] * num_features

            # Initialize hyperparameters
            weight_alpha = 1 / (num_games * num_features *
                                weight_alpha_divider)  # weight learning rate
            # ADJUST IF NEW FEATURES ADDED/DELETED
            rolling_feature_sum = feature_values[0][0:num_features - roster_size]
            # feature learning rate
            feature_alpha = 1 / \
                (num_games * num_features * feature_alpha_divider)

            # Train weights on first (num_games - 10) games of the player's season
            for game in range(num_games - 10):
                prediction = 0
                for feature in range(num_features):
                    if game > 0 and feature < num_features - roster_size:
                        rolling_feature_sum[feature] += (feature_alpha * feature_values[game][feature]) - (
                            feature_alpha * rolling_feature_sum[feature])
                    prediction += feature_values[game][feature] * \
                        weights[feature]
                difference = actual_stats[game] - prediction
                for weight in range(num_features):
                    weights[weight] += weight_alpha * \
                        difference * feature_values[game][weight]

            # TO DO: ADD GAMES FROM PREVIOUS SEASONS WITH HYPERPARAMETER TO WEIGH
            # DOWN PREVIOUS SEASONS/TEAMS
            player_feature_dict[player_name] = (
                feature_values, weights, actual_stats, rolling_feature_sum, opp_team_list)

    # Return dictionary of each player's features, weights, and actual points
    return player_feature_dict


def evaluate_players(player_feature_dict, team_dict, start_games_from_end, end_games_from_end, step):
    """
    Evaluates the predicted stat for each player in player_feature_dict
    versus their actual stat achieved from (including) start_games_from_end
    from the end to (excluding) end_games_from_end from the end by using every
    step game. team_dict is a dictionary from each team to their average stats
    for the season using an exponential rolling average.

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
        actual_stats = player_feature_dict[player][2]
        rolling_features = player_feature_dict[player][3]
        opp_team_list = player_feature_dict[player][4]
        num_features = len(feature_values[0])
        num_evaluation_games = math.ceil(
            (start_games_from_end - end_games_from_end) / 2)
        start_game = num_games - start_games_from_end
        end_game = num_games - end_games_from_end

        # Get prediction for stats for each of the specified games
        final_prediction = [0] * num_evaluation_games
        real_stats = []
        count = 0
        for game in range(start_game, end_game, step):
            opposing_team = opp_team_list[game]
            for feature in range(34):
                final_prediction[count] += rolling_features[feature] * \
                    weights[feature]
            for feature in range(34, 69):
                final_prediction[count] += team_dict[opposing_team][feature -
                                                                    34] * weights[feature]
            for feature in range(69, num_features):
                final_prediction[count] += feature_values[game][feature] * \
                    weights[feature]
            real_stats.append(actual_stats[game])
            count += 1

        # Compute the predicted vs average stats and add to result dict
        predicted = sum(final_prediction) / num_evaluation_games
        actual = sum(real_stats) / num_evaluation_games
        results[player] = (predicted, actual)

    return results


def validation(stat, player_list, team_list, random_tests, weight_alpha=None, feature_alpha=None, opp_team_alpha=None):
    """
    Randomly test different learning rates and initial weights to find and
    return the best performing hyperparameters based on least squares on
    player_list. Tests each hyperparameter on random_tests number of random
    values. Validates on each players 10th, 8th, 6th, 4th, and 2nd to last
    games of the season.

    You can specify weight_alpha, feature_alpha, and opp_team_alpha when
    calling the function. The specified hyperparameters will be set and not
    randomly tested.
    """
    # Generate random number for the divider of alpha (learning rate)
    if weight_alpha == None:
        random_weight_dividers = []
    else:
        random_weight_dividers = [weight_alpha]
    if feature_alpha == None:
        random_feature_dividers = []
    else:
        random_feature_dividers = [feature_alpha]
    if opp_team_alpha == None:
        random_opp_team_dividers = []
    else:
        random_opp_team_dividers = [opp_team_alpha]
    for i in range(random_tests):
        if weight_alpha == None:
            random_weight_dividers.append(random.randint(1, 1000))
        if feature_alpha == None:
            random_feature_dividers.append(random.randint(1, 1000))
        if opp_team_alpha == None:
            random_opp_team_dividers.append(random.randint(1, 1000))

    # Find the most accurate divider
    best_dividers = (1, 1, 1)
    best_divider_lss = float('inf')
    for weight_divider in random_weight_dividers:
        for feature_divider in random_feature_dividers:
            for opp_team_divider in random_opp_team_dividers:
                # Train model using divider
                player_feature_dict = train_players(
                    stat, player_list, weight_divider, feature_divider)

                # Get exponential rolling average of opposing team stats
                team_dict = {}
                for team in team_list:
                    team_dict[team.name] = get_opp_team_stats(
                        team, opp_team_divider)

                # Evaluate model using divider
                results = evaluate_players(
                    player_feature_dict, team_dict, 10, 0, 2)

                # Check if this divider is the best one so far using least squares sum
                ls_sum = 0
                for player in results.keys():
                    ls_sum += abs(results[player][0] - results[player][1]) ** 2

                if ls_sum < best_divider_lss:
                    best_dividers = (
                        weight_divider, feature_divider, opp_team_divider)
                    best_divider_lss = ls_sum

    return best_dividers


def test_players(player_feature_dict, team_dict):
    """
    Test features and weights in player_feature_dict for each player with
    opposing teams' stats in team_dict. Tests on each player's 9th, 7th, 5th,
    3rd and last games of the season and outputs the model's predicted stats
    vs player's actual stats for these games of the player's season.
    """
    results = evaluate_players(player_feature_dict, team_dict, 9, 0, 2)

    for player in results.keys():
        # Output the predicted vs average stats and write to file
        output_string1 = player + " average predicted stats: " + \
            str(results[player][0])
        output_string2 = player + " actual average stats: " + \
            str(results[player][1])
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
    if team_games[0].home_team == team_name:
        home = True
    else:
        home = False
    if home == True:
        average_stats_str = list(team_games[0].home_team_stats.values())
    else:
        average_stats_str = list(team_games[0].away_team_stats.values())
    average_stats = []
    for value in average_stats_str:
        new_value = convert_to_valid_value(value)
        average_stats.append(new_value)
    for game in range(1, len(team_games)):
        if team_games[game].home_team == team_name:
            home = True
        else:
            home = False
        if home == True:
            team_stats = team_games[game].home_team_stats
            team_inactives = team_games[game].home_inactives  # team inactives
        else:
            team_stats = team_games[game].away_team_stats
            team_inactives = team_games[game].away_inactives

        team_stat_list = list(team_stats.values())
        team_features = []
        for value in team_stat_list:
            # Convert stats to valid floats
            new_value = convert_to_valid_value(value)
            team_features.append(new_value)

        alpha = 1 / (82 * 35 * learning_rate)
        for feature in range(len(team_features)):
            average_stats[feature] += (alpha * team_features[feature]) - \
                (alpha * average_stats[feature])

    return average_stats


def run_model(file, stat, hyperparameters=None):
    """
    Train, validate, and test the reinforcement learning model for stat on the
    2022 NBA season. Output the results in file. Validation only occurs if
    hyperparameters is not specified. If hyperparameters is specified
    (weight_divider, feature_divider, opp_team_divider), then validation
    does not occur and the hyperparameters passed in are used.
    """
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
            # Add all teams to team_list
            player_team = player_var.team
            if player_team not in team_list:
                team_list.append(player_team)

            if player_var.team.name == "GSW":
                gamelog_list.append(player_var)

    # Find best hyperparameters
    if hyperparameters == None:
        best_hyperparameters = validation(stat, gamelog_list, team_list, 30)
        with open(file, "a") as file:
            file.write("Best weight alpha found: " +
                    str(best_hyperparameters[0]) + "\n")
            file.write("Best feature alpha found: " +
                    str(best_hyperparameters[1]) + "\n")
            file.write("Best opposing team alpha found: " +
                    str(best_hyperparameters[2]) + "\n")
    else:
        best_hyperparameters = hyperparameters

    # Train model using best hyperparameter
    team_dict = {}
    for team in team_list:
        team_dict[team.name] = get_opp_team_stats(
            team, best_hyperparameters[2])
    player_dict = train_players(
        stat, gamelog_list, best_hyperparameters[0], best_hyperparameters[1])

    # Evaluate model
    test_players(player_dict, team_dict)
