import numpy as np
import pickle
import joblib
import logging
from getting_bbref_season_data import Player, Season, Team, Game
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from reinforcement_learning_model import extract_features_and_targets
from sklearn.model_selection import GridSearchCV
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.preprocessing import StandardScaler
import joblib
import logging

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
    # Load and preprocess data
    features, targets = load_and_preprocess_data(stat)

    # Train and evaluate model
    train_and_evaluate_model(features, targets, file)


def load_and_preprocess_data(stat):
    try:
        with open('s2022.pkl', 'rb') as inp:
            s2022 = pickle.load(inp)
        with open('players.pkl', 'rb') as inp:
            players = pickle.load(inp)
    except FileNotFoundError as e:
        logging.error(f"Failed to load data: {str(e)}")
        return

    # Find the predicted stats for every player in the season
    gamelog_list = []
    for player in players:
        player_var = players[player]
        if player_var.year == 2022 and player_var.team.name == "GSW":
            gamelog_list.append(player_var)

    # Extract features and targets
    features, targets = extract_features_and_targets(gamelog_list, stat)
    features = [[convert_to_valid_value(value) for value in row] for row in features]

    return features, targets

def train_and_evaluate_model(features, targets, output_file):
    # Split the dataset into training and testing sets
    X_train, X_test, y_train, y_test = train_test_split(features, targets, test_size=0.2, random_state=42)

    # Apply feature scaling
    scaler = StandardScaler()
    X_train = scaler.fit_transform(X_train)
    X_test = scaler.transform(X_test)

    # Hyperparameters grid
    param_grid = {
        'n_estimators': [50, 100, 200],
        'max_depth': [None, 10, 20, 30],
        'min_samples_split': [2, 5, 10],
        'min_samples_leaf': [1, 2, 4]
    }

    # Create a machine learning model using the chosen algorithm
    model = RandomForestRegressor(random_state=42)

    # Hyperparameters tuning using Grid Search
    grid_search = GridSearchCV(estimator=model, param_grid=param_grid, cv=3, n_jobs=-1, verbose=2)
    grid_search.fit(X_train, y_train)

    best_model = grid_search.best_estimator_

    # Train the model using the training data
    best_model.fit(X_train, y_train)

    # Test the model's performance using the testing data
    y_pred = best_model.predict(X_test)

    # Evaluate the model's performance using a chosen metric
    mae = mean_absolute_error(y_test, y_pred)
    mse = mean_squared_error(y_test, y_pred)
    r2 = r2_score(y_test, y_pred)

    # Log the evaluation metrics
    logging.info(f"Mean Absolute Error: {mae:.2f}")
    logging.info(f"Mean Squared Error: {mse:.2f}")
    logging.info(f"R2 Score: {r2:.2f}")

    # Save the trained model for future use
    joblib.dump(best_model, 'nba_model.pkl')

    # Output the results to the output file
    try:
        with open(output_file, "a") as f:
            f.write("Best Model Parameters: " + str(grid_search.best_params_) + "\n")
            f.write(f"Mean Absolute Error: {mae:.2f}\n")
            f.write(f"Mean Squared Error: {mse:.2f}\n")
            f.write(f"R2 Score: {r2:.2f}\n")
    except IOError as e:
        logging.error(f"Failed to write results to file: {str(e)}")

    # Check feature importance
    feature_importances = best_model.feature_importances_
    logging.info("Feature importances: " + str(feature_importances))