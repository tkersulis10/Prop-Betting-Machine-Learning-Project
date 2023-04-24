import numpy as np
import pickle
from getting_bbref_season_data import Player, Season, Team, Game
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split
from getting_bbref_season_data import Player, Season, Team, Game
from reinforcement_learning_model import extract_features_and_targets

def convert_to_valid_value(value):
    """
    Convert the value from an invalid string to a valid float.
    """
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
    return float(value)

def run_model(file, stat):
    """
    Train, validate, and test the reinforcement learning model for stat on the
    2022 NBA season. Output the results in file.
    """
    with open('s2022.pkl', 'rb') as inp:
        s2022 = pickle.load(inp)
    with open('players.pkl', 'rb') as inp:
        players = pickle.load(inp)

    # Find the predicted stats for every player in the season
    gamelog_list = []
    team_list = []
    for player in players:
        player_var = players[player]
        if player_var.year == 2022:
            # Add all teams to team_list
            player_team = player_var.team
            if player_team not in team_list:
                team_list.append(player_team)

            if player_var.team.name == "GSW":
                gamelog_list.append(player_var)

    # Extract features and targets
    features, targets = extract_features_and_targets(gamelog_list, stat)

    # Process features with convert_to_valid_value function
    features = [[convert_to_valid_value(value) for value in row] for row in features]

    # Split the dataset into training and testing sets
    from sklearn.model_selection import train_test_split
    X_train, X_test, y_train, y_test = train_test_split(features, targets, test_size=0.2, random_state=42)

    # Create a machine learning model using the chosen algorithm
    from sklearn.ensemble import RandomForestRegressor
    model = RandomForestRegressor(n_estimators=100, random_state=42)

    # Train the model using the training data
    model.fit(X_train, y_train)

    # Test the model's performance using the testing data
    y_pred = model.predict(X_test)

    # Evaluate the model's performance using a chosen metric
    from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
    mae = mean_absolute_error(y_test, y_pred)
    mse = mean_squared_error(y_test, y_pred)
    r2 = r2_score(y_test, y_pred)

    # Print the evaluation metrics
    results = f"Mean Absolute Error: {mae:.2f}\nMean Squared Error: {mse:.2f}\nR2 Score: {r2:.2f}\n"

    # Save the trained model for future use
    import joblib
    joblib.dump(model, 'nba_model.pkl')

    # Output the results to the output file
    with open(file, "a") as f:
        f.write("Stat: " + stat + "\n")
        f.write(results)