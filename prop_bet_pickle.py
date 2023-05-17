import pickle
import pickle5

class Stat:
    def __init__(self, filename):
        self.file_name = filename
        self.player_props = {}

    def __repr__(self):
        return str(self.__dict__)
    
    def getPlayerProps(self):
        with open(self.file_name) as file:
            lines = file.readlines()
            current_date = ""
            for line in lines:
                if line[0:4] == "Date":
                    current_date = line[6:-1]
                    self.player_props[current_date] = []
                elif line[2:8] == "Player":
                    # new_line = line[12:].split(", ")
                    first_comma = line.index(",")
                    first_at = line.index("@")
                    player_id = line[12:first_comma - 1]
                    player_line = line[first_comma + 31:first_at]
                    player_odds = line[first_at + 1:first_at + 5]
                    if player_odds[3] == "\\":
                        player_odds = "+" + player_odds[:3]
                    # self.player_props[current_date].append((new_line[0], new_line[1][8:], new_line[2][7:11]))
                    self.player_props[current_date].append((player_id, player_line, player_odds))

# points = Stat("points_prop_lines_raw.txt")
# points.getPlayerProps()
# with open('points_prop_bets.pkl', 'wb') as outp:
#     pickle.dump(points.player_props, outp, pickle.HIGHEST_PROTOCOL)

# assists = Stat("assists_prop_lines_raw.txt")
# assists.getPlayerProps()
# with open('assists_prop_bets.pkl', 'wb') as outp:
#     pickle.dump(assists.player_props, outp, pickle.HIGHEST_PROTOCOL)

# rebounds = Stat("rebounds_prop_lines_raw.txt")
# rebounds.getPlayerProps()
# with open('rebounds_prop_bets.pkl', 'wb') as outp:
#     pickle.dump(rebounds.player_props, outp, pickle.HIGHEST_PROTOCOL)

# Example Usage:
# points_date_dict = {}
# with open('points_prop_bets.pkl', 'rb') as inp:
#     points_date_dict = pickle.load(inp)
# print(points_date_dict['1-6-2021'])
                    
    
        