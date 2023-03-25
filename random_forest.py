import pickle
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error

# Load the saved player data
with open('players.pkl', 'rb') as inp:
    players = pickle.load(inp)

# Define the players and their corresponding names
player_data = [
    (players['StephenCurry2022GSW'].gamelog, "Stephen Curry"),
    # Add the other players here...
]

# Function to preprocess the player data
def preprocess_player_data(player_data):
    features = list(player_data[0].keys())
    features.pop(18)

    actual_points = []
    feature_values_floats = []

    for i in range(82):
        if type(player_data[i]) != str:
            feature_values = list(player_data[i].values())
            actual_points.append(int(feature_values.pop(18)))

            feature_values_floats.append([])

            for value in feature_values:
                time = value.find(":")
                decimal = value.find(".")
                plus = value.find("+")

                if value == "":
                    value = 0

                if time >= 0:
                    value = int(value[0:time]) + (int(value[time + 1:5]) / 60)

                if decimal == 0:
                    value = "0" + value

                if plus == 0:
                    value = value[1:]

                feature_values_floats[-1].append(float(value))

    return np.array(feature_values_floats), np.array(actual_points)

# Train and test the Random Forest Regressor for each player
for player, name in player_data:
    X, y = preprocess_player_data(player)
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    # Create and train the Random Forest Regressor
    rfr = RandomForestRegressor(n_estimators=100, random_state=42)
    rfr.fit(X_train, y_train)

    # Make predictions and calculate the mean squared error
    y_pred = rfr.predict(X_test)
    mse = mean_squared_error(y_test, y_pred)

    # Print the results
    output_string = f"{name}: Mean Squared Error = {mse}"
    print(output_string)

    # Write the output_string to the "random_forest_output.txt" file
    with open("random_forest_output.txt", "a") as file:
        file.write(output_string + "\n")