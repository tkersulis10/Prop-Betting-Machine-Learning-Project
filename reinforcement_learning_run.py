from getting_bbref_season_data import Player
from getting_bbref_season_data import Season
from getting_bbref_season_data import Team
from getting_bbref_season_data import Game
from reinforcement_learning_model import run_model

output_file = "reinforcement_learning_output.txt"
stat_dict = {"pts": 18, "ast": 13, "trb": 12, "fg": 1,
            "3p": 4, "ft": 7, "stl": 14, "blk": 15, "tov": 16}
hyperparameters_dict = {"pts": (148, 30, 9), "ast": (699, 29, 914), "trb": (417, 8, 119)}

def run(player_name, stat_run_list):
    # stat_run_list = ["pts"]
    # output_string = ""
    output_list = []
    for stat in stat_run_list:
        with open(output_file, "a") as file:
            file.write("Stat: " + stat + "\n")
        # output_string += "Stat: " + stat + "\n"
        curr_stat_list = []
        curr_stat_list.append(("Stat: " + stat, None, None, None))
        model_output = run_model(player_name, output_file, stat_dict[stat], hyperparameters=hyperparameters_dict[stat])
        # if model_output[player_name] == ["Not a valid player's name.\nMake sure to capitalize their first and last names."]:
        if model_output == None:
            # return model_output[player_name]
            return None
        # output_string += model_output
        curr_stat_list += model_output[player_name]
        output_list.append(curr_stat_list)

    # return output_string
    return output_list
# run("Stephen Curry")