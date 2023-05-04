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
                    current_date = line[6:]
                elif line[0:6] == "Player":
                    new_line = line[8:].split(", ")
                    self.player_props[current_date] = (new_line[0], new_line[1][8:], new_line[2][7:11])

points = Stat("points_prop_bet_output.txt")
points.getPlayerProps()
with open('points_prop_bets.pkl', 'wb') as outp:
    pickle.dump(points.player_props, outp, pickle.HIGHEST_PROTOCOL)

points_date_dict = {}
with open('points_prop_bets.pkl', 'rb') as inp:
    points_date_dict = pickle.load(inp)

print(points_date_dict['1-6-2021'])
                    
    
        