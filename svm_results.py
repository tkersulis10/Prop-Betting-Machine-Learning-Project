import pickle
def run(player_name, stat_run_list):
    results = []
    for stat in stat_run_list:
        if stat == "pts":
            with open('svm_test_map_points.pkl', 'rb') as inp:
                test_players = pickle.load(inp)
                results.append(test_players[player_name])
        elif stat == "trb":
            with open('svm_test_map_rebounds.pkl', 'rb') as inp:
                test_players = pickle.load(inp)
                results.append(test_players[player_name])
        elif stat == "ast":
            with open('svm_test_map_assists.pkl', 'rb') as inp:
                test_players = pickle.load(inp)
                results.append(test_players[player_name])
    return results