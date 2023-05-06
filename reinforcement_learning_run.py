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
    """
    Runs the reinforcement_learning_model on player_name on the stats in
    stat_run_list. If there is an error (i.e. with the player's name being
    incorrect) returns None. Otherwise, returns a list of lists in the
    following format:
    Each nested list is for a different stat in stat_run_list. The first
    element of each of these lists is "Stat: " + stat. The remaining elements
    of the lists are the outputs to reinforcement_learning_model.run_model.
    These outputs are dictionaries where the keys are player_name and values
    are the result of reinforcement_learning_model.test_players (and
    evaluate_player).

    Example output for player_name = 'Stephen Curry' and stat_run_list = ['pts,
    'ast']:
    [
        [
            'Stat: pts', '25.417420378003563', '14.8', ['24.1', '24.1', '24.9', '25.7', '28.0'], 
            ['27', '21', '15', '8', '3'], 
            ['Sun, Feb 27, 2022', 'Thu, Mar 3, 2022', 'Tue, Mar 8, 2022', 'Sat, Mar 12, 2022', 'Wed, Mar 16, 2022']
        ], 
        [
            'Stat: ast', '5.84271791785162', '6.8', ['5.55', '5.55', '5.72', '5.92', '6.45'],
            ['10', '9', '5', '8', '2'],
            ['Sun, Feb 27, 2022', 'Thu, Mar 3, 2022', 'Tue, Mar 8, 2022', 'Sat, Mar 12, 2022', 'Wed, Mar 16, 2022']
        ]
    ]

    Outer list is two elements because two stats are given.
    Inner lists are stat labels, predicted average stat over games, actual
    average stat over games, list of predicted stat for each game,
    list of actual stat for each game, list of dates for the games.
    """
    # stat_run_list = ["pts"]
    # output_string = ""
    output_list = []
    for stat in stat_run_list:
        with open(output_file, "a") as file:
            file.write("Stat: " + stat + "\n")
        # output_string += "Stat: " + stat + "\n"
        curr_stat_list = []
        curr_stat_list.append("Stat: " + stat)
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