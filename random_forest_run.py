from random_forest_model import run_model

output_file = "random_forest_output.txt"
stat_dict = {"pts": 18, "ast": 13, "trb": 12, "fg": 1,
             "3p": 4, "ft": 7, "stl": 14, "blk": 15, "tov": 16}
stat_run_list = ["pts", "ast", "trb"]
for stat in stat_run_list:
    run_model(output_file, stat_dict[stat])