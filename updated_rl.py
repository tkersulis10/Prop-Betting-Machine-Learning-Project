import pickle
import getting_bbref_season_data


def process_gamelog(player):
    # Find the index of the first valid game in the player's gamelog
    game_count = 0
    while type(player[game_count]) == str:
        game_count += 1

    # Extract feature names and remove the 18th feature (points)
    features = list(player[game_count].keys())
    features.pop(18)

    # Initialize lists to store actual points and feature values
    actual_points = []
    feature_values_floats = []

    # Iterate through each game in the player's gamelog
    for i in range(82):
        if type(player[i]) != str:
            feature_values = list(player[i].values())
            # Store actual points and remove from the feature_values list
            actual_points.append(int(feature_values.pop(18)))

            # Convert feature values to floats and store them in feature_values_floats
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
                feature_values_floats[len(feature_values_floats) - 1].append(float(value))

    return features, actual_points, feature_values_floats

def predict_points(features, actual_points, feature_values_floats):
    num_features = len(features)
    weights = [0] * num_features
    num_games = len(feature_values_floats)
    alpha = 1 / (num_games * 500)  # Learning rate hyperparameter

    # Update weights based on the difference between actual points and prediction
    for game in range(num_games - 5):
        prediction = 0
        for feature in range(num_features):
            prediction += feature_values_floats[game][feature] * weights[feature]
        difference = actual_points[game] - prediction

        for weight in range(num_features):
            weights[weight] += alpha * difference * feature_values_floats[game][weight]

    # Calculate the predicted points for the last 5 games
    final_prediction = [0] * 5
    count = 0
    for game in range(num_games - 5, num_games):
        for feature in range(num_features):
            final_prediction[count] += feature_values_floats[game][feature] * weights[feature]
        count += 1

    return final_prediction


with open('players.pkl', 'rb') as inp:
    players = pickle.load(inp)

# Create a list of players' gamelogs and their names
gamelog_list = []
# Add each player's gamelog and name to the list
# ...

for player, name in gamelog_list:
    # Process the player's gamelog to extract features, actual points, and feature values
    features, actual_points, feature_values_floats = process_gamelog(player)
    # Predict points for the last 5 games
    final_prediction = predict_points(features, actual_points, feature_values_floats)

    # Calculate the average predicted points and print the result
    output_string = name + " average predicted points: " + str(sum(final_prediction) / len(final_prediction))
    print(output_string)

    # Write the output_string to the "reinforcement_learning_output.txt" file
    with open("reinforcement_learning_output.txt", "a") as file:
        file.write(output_string + "\n")