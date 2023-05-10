from getting_bbref_season_data import Player
from getting_bbref_season_data import Season
from getting_bbref_season_data import Team
from getting_bbref_season_data import Game
import reinforcement_learning_run
import pickle
import pickle5
import random
import get_prop_bets
from unidecode import unidecode

with open('players.pkl', 'rb') as inp:
    try:
        players = pickle.load(inp)
    except:
        players = pickle5.load(inp)

players_2022 = []
test_year = 2022 # variable to change
for player in players:
    if players[player].year == test_year:
        players_2022.append(players[player])

# Test model on 200 random players from 2022 NBA season
total_num_players = len(players_2022)
num_random_players = 10 # variable to change
random_players = random.choices(players_2022, k=num_random_players)
stat_list = ['pts', 'ast', 'trb']
player_count = 0
pts_diff = 0
ast_diff = 0
trb_diff = 0
correct_count_pts = 0
correct_count_ast = 0
correct_count_trb = 0
total_num_dates_pts = 0
total_num_dates_ast = 0
total_num_dates_trb = 0
for player in random_players:
    # run model
    player_name = unidecode(player.name)
    print(player_name)
    results = reinforcement_learning_run.run(player.name, stat_list)
    if results != None:
        player_count += 1
        pts_diff += abs(float(results[0][1]) - float(results[0][2]))
        ast_diff += abs(float(results[1][1]) - float(results[1][2]))
        trb_diff += abs(float(results[2][1]) - float(results[2][2]))
        num_dates = len(results[0][5])
        for date_count in range(num_dates):
            prop_output = get_prop_bets.get_props(player_name, 'pts', results[0][5][date_count])
            if prop_output != None:
                total_num_dates_pts += 1
                prop_line_pts = float(prop_output[0])
                predicted_pts = float(results[0][3][date_count])
                real_pts = float(results[0][4][date_count])
                if predicted_pts > prop_line_pts:
                    if real_pts >= prop_line_pts:
                        correct_count_pts += 1
                else:
                    if real_pts <= prop_line_pts:
                        correct_count_pts += 1
            
            prop_output = get_prop_bets.get_props(player_name, 'ast', results[1][5][date_count])
            if prop_output != None:
                total_num_dates_ast += 1
                prop_line_ast = float(prop_output[0])
                predicted_ast = float(results[1][3][date_count])
                real_ast = float(results[1][4][date_count])
                if predicted_ast > prop_line_ast:
                    if real_ast >= prop_line_ast:
                        correct_count_ast += 1
                else:
                    if real_ast <= prop_line_ast:
                        correct_count_ast += 1

            prop_output = get_prop_bets.get_props(player_name, 'trb', results[2][5][date_count])
            if prop_output != None:
                total_num_dates_trb += 1
                prop_line_trb = float(prop_output[0])
                predicted_trb = float(results[2][3][date_count])
                real_trb = float(results[2][4][date_count])
                if predicted_trb > prop_line_trb:
                    if real_trb >= prop_line_trb:
                        correct_count_trb += 1
                else:
                    if real_trb <= prop_line_trb:
                        correct_count_trb += 1

average_diff_pts = pts_diff / player_count
average_diff_ast = ast_diff / player_count
average_diff_trb = trb_diff / player_count
correct_pts_ratio = correct_count_pts / total_num_dates_pts
correct_ast_ratio = correct_count_ast / total_num_dates_ast
correct_trb_ratio = correct_count_trb / total_num_dates_trb

with open("test_model_output.txt", "a") as file:
    file.write("Testing reinforcement learning model...\n") # model to test on
    file.write("Testing on " + str(num_random_players) + " random players from the " \
               + str(test_year) + " NBA season.\n")
    file.write("Average pts difference: " + str(average_diff_pts) + "\n")
    file.write("Average ast difference: " + str(average_diff_ast) + "\n")
    file.write("Average trb difference: " + str(average_diff_trb) + "\n")
    file.write("Ratio of correct pts bets: " + str(correct_pts_ratio) + "\n")
    file.write("Ratio of correct ast bets: " + str(correct_ast_ratio) + "\n")
    file.write("Ratio of correct trb bets: " + str(correct_trb_ratio) + "\n")
