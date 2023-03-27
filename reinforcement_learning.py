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
gamelog_list.append(players['JeffDowtin2022GSW'])
gamelog_list.append(players['QuinndaryWeatherspoon2022GSW'])

def train_players(player_list):
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
        alpha = 1 / (num_games * num_features * 100) # learning rate

        # Train weights on first (num_games - 5) games of the player's season
        for game in range(num_games - 5):
            prediction = 0
            for feature in range(num_features):
                prediction += feature_values[game][feature] * weights[feature]
            difference = actual_points[game] - prediction
            for weight in range(num_features):
                weights[weight] += alpha * difference * feature_values[game][weight]

        player_feature_dict[player_name] = (feature_values, weights, actual_points)
    
    # Return dictionary of each player's features, weights, and actual points
    return player_feature_dict


def test_players(player_feature_dict):
    """
    Test features and weights in feature_values on all of the players in
    player_list. Tests on each player's last 5 games of the season and outputs
    the model's predicted points vs player's actual points for the last 5
    games of the player's season.
    """
    for player in player_feature_dict.keys():
        # Initialize needed variables
        num_games = len(player_feature_dict[player][0])
        feature_values = player_feature_dict[player][0]
        weights = player_feature_dict[player][1]
        actual_points = player_feature_dict[player][2]
        num_features = len(feature_values[0])

        # Get prediction for points for each of the last 5 games
        final_prediction = [0] * 5
        count = 0
        for game in range(num_games - 5, num_games):
            for feature in range(num_features):
                final_prediction[count] += feature_values[game][feature] * weights[feature]
            count += 1

        # Output the predicted vs average points and write to file
        output_string1 = player + " average predicted points: " + str(sum(final_prediction) / len(final_prediction))
        output_string2 = player + " actual average points: " + str(sum(actual_points[num_games - 5:]) / 5)
        with open("reinforcement_learning_output.txt", "a") as file:
            file.write(output_string1 + "\n")
            file.write(output_string2 + "\n")

player_dict = train_players(gamelog_list)
test_players(player_dict)