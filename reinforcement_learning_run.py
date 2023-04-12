from getting_bbref_season_data import Player
from getting_bbref_season_data import Season
from getting_bbref_season_data import Team
from getting_bbref_season_data import Game
from reinforcement_learning_model import run_model

output_file = "reinforcement_learning_output.txt"
stat_dict = {"pts": 18, "ast": 13, "trb": 12, "fg": 1,
             "3p": 4, "ft": 7, "stl": 14, "blk": 15, "tov": 16}
stat_run_list = ["pts", "ast", "trb"]
for stat in stat_run_list:
    with open(output_file, "a") as file:
        file.write("Stat: " + stat + "\n")
    run_model(output_file, stat_dict[stat])
