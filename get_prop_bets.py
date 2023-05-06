import pickle
import pickle5
from prop_bet_pickle import Stat

month_dict = {"Jan": "1", "Feb": "2", "Mar": "3", "Apr": "4", "May": "5", "Jun": "6",
              "Jul": "7", "Aug": "8", "Sep": "9", "Oct": "10", "Nov": "11", "Dec": "12"}

def get_props(player_name, stat, date):
    """
    Get the prop bets for stat for player_name for date.
    """
    if stat == "pts":
        try:
            with open('points_prop_bets.pkl', 'rb') as inp:
                props = pickle.load(inp)
        except: # For Python 3.7
            with open('points_prop_bets.pkl', 'rb') as inp:
                props = pickle5.load(inp)
    elif stat == "ast":
        try:
            with open('assists_prop_bets.pkl', 'rb') as inp:
                props = pickle.load(inp)
        except: # For Python 3.7
            with open('assists_prop_bets.pkl', 'rb') as inp:
                props = pickle5.load(inp)
    elif stat == "trb":
        try:
            with open('rebounds_prop_bets.pkl', 'rb') as inp:
                props = pickle.load(inp)
        except: # For Python 3.7
            with open('rebounds_prop_bets.pkl', 'rb') as inp:
                props = pickle5.load(inp)
    else:
        return None
    try:
        space_index = player_name.index(" ")
    except:
        return None
    new_name = player_name[0:1] + " " + player_name[space_index + 1:]
    new_date = ""
    space_index = date.index(" ")
    new_date += month_dict[date[space_index + 1: space_index + 4]] + "-"
    new_date += date[space_index + 5: -6] + "-"
    new_date += date[-4:]
    for player in props[new_date]:
        space_index = player[0].index(" ")
        if new_name == player[0][0:1] + " " + player[0][space_index + 1:]:
            return (player[1], player[2])

    return None

# print(get_props("Stephen Curry", "pts", "Sun, Feb 27, 2022"))