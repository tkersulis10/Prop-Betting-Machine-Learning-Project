import getting_prop_bet_data

with open("rebounds_prop_bet_output.txt") as file:
    lines = file.readlines()
    previous = "hi"
    empty_lines = []
    for line in lines:
        if previous[0:4] == "Date" and line == "\n":
            date = previous[6:-1]
            year = date[-4:]
            # new_date = date[-4:] + "-"
            dash_index = date.index("-")
            #if dash_index == 1:
                #new_date += "0" + date[:dash_index] + "-"
            month = date[:dash_index]
            #else:
            #    new_date += date[:dash_index] + "-"
            #next_dash_index = date[dash_index + 1:].index("-")
            day = date[dash_index + 1:-5]
            #if next_dash_index == 1:
            #    new_date += "0" + date[-6:-5]
            #else:
            #    new_date += date[-7:-5]
            empty_lines.append((int(year), int(month), int(day)))
        previous = line

getting_prop_bet_data.get_data("points", date_list=empty_lines)
getting_prop_bet_data.get_data("assists", date_list=empty_lines)
getting_prop_bet_data.get_data("rebounds", date_list=empty_lines)