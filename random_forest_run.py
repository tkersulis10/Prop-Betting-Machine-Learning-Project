from random_forest_model import run_model

output_file = "random_forest_output.txt"
stat_dict = {"pts": 18, "ast": 13, "trb": 12, "fg": 1,
             "3p": 4, "ft": 7, "stl": 14, "blk": 15, "tov": 16}
stat_run_list = ["pts", "ast", "trb"]

def run(player_name, stat_run_list):
    output_list = []
    for stat in stat_run_list:
        with open(output_file, "a") as file:
            file.write("Stat: " + stat + "\n")
        curr_stat_list = []
        curr_stat_list.append("Stat: " + stat)
        model_output = run_model(player_name, output_file, stat_dict[stat])
        if model_output == None:
            return None
        curr_stat_list += model_output[player_name]
        output_list.append(curr_stat_list)
    return output_list