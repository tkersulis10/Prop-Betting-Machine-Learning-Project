# Features

# [PRIORS] - scraped from https://projects.fivethirtyeight.com/2022-nba-player-projections/klay-thompson/
# point guard (0 or 1)
# shooting guard (0 or 1)
# small forward (0 or 1)
# power forwards (0 or 1)
# center (0 or 1)
# experience in years
# age
# height in inches
# weight in pounds
# draft position
# true shooting%
# free throw%
# Usage %
# 3pt frequency
# ft frequency
# assist %
# turnover %
# rebound %
# block %
# steal %
# defensive +/-
# ppg from most recent season

# [SEASON STATS]
# of games played
# true shooting%
# free throw%
# 3pt frequency
# ft frequency
# points average
# fga average
# minutes played average
# 20% percentile points
# 40% percentile points
# 50% percentile points
# 60% percentile points
# 80% percentile points
# 20% percentile fga
# 40% percentile fga
# 50% percentile fga
# 60% percentile fga
# 80% percentile fga
# 20% percentile usage
# 40% percentile usage
# 50% percentile usage
# 60% percentile usage
# 80% percentile usage
# 20% percentile minutes played
# 40% percentile minutes played
# 50% percentile minutes played
# 60% percentile minutes played
# 80% percentile minutes played

# [RECENT FORM 1] - 1 game sliding window
# points
# fga
# usage
# mp
# true shooting%
# free throw%
# 3pt frequency
# ft frequency

# [RECENT FORM 2] - 2 game sliding window
# 1st least points
# 2nd least points
# 1st least fga
# 2nd least fga
# 1st least usage
# 2nd least usage
# 1st least mp
# 2nd least mp
# true shooting%
# free throw%
# 3pt frequency
# ft frequency

# [RECENT FORM 3] - 4 game sliding window
# 4 games available (0 or 1)
# 1st least points
# 2nd least points
# 3rd least points
# 4th least points
# 1st least fga
# 2nd least fga
# 3rd least fga
# 4th least fga
# 1st least usage
# 2nd least usage
# 3rd least usage
# 4th least usage
# 1st least mp
# 2nd least mp
# 3rd least mp
# 4th least mp
# true shooting%
# free throw%
# 3pt frequency
# ft frequency

# [RECENT FORM 4] - 8 game sliding window
# 8 games available (0 or 1)
# 1st least points
# 2nd least points
# 3rd least points
# 4th least points
# 5th least points
# 6th least points
# 7th least points
# 8th least points
# 1st least fga
# 2nd least fga
# 3rd least fga
# 4th least fga
# 5th least fga
# 6th least fga
# 7th least fga
# 8th least fga
# 1st least usage
# 2nd least usage
# 3rd least usage
# 4th least usage
# 5th least usage
# 6th least usage
# 7th least usage
# 8th least usage
# 1st least mp
# 2nd least mp
# 3rd least mp
# 4th least mp
# 5th least mp
# 6th least mp
# 7th least mp
# 8th least mp
# true shooting%
# free throw%
# 3pt frequency
# ft frequency

# [GAME STATE] TODO: add team pace metrics, and foul/free throw metrics
# home or road (0 or 1)
# team game number
# opponent game number
# team offensive rating season
# team offensive rating last 8 games
# team defensive rating season
# team defensive rating last 8 games
# opponent offensive rating season
# opponent offensive rating last 8 games
# opponent defensive rating season
# opponent defensive rating last 8 games

# TODO: [INJURY STATE] which teammates are injured, which teammates are coming back from injury, and how that affects this player's usage, relative to their historical stats

import numpy as np
import json
from random import shuffle
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC

feature_vectors = open("svm_feature_vectors.txt", "r")
lis = []
for line in feature_vectors:
    json_obj = json.loads(line)
    lis.append(json_obj)
shuffle(lis)
train_list = [element['feature_vector'] for element in lis[:-50]]
train_labels = [element['label'] for element in lis[:-50]]
test_list = [element['feature_vector'] for element in lis[-50:]]
test_labels = [element['label'] for element in lis[-50:]]
train_X = np.array(train_list)
train_Y = np.array(train_labels)
test_X = np.array(test_list)


clf = make_pipeline(StandardScaler(), SVC(gamma='auto'))
clf.fit(train_X, train_Y)

f = open("svm_predictions.txt", "a")

for i in range(len(lis)-51, len(lis)):
    f.write(lis[i]["Player"] + " " +  lis[i]["date"] + " " + lis[i]["lines"] + " prediction: " + str(clf.predict([lis[i]["feature_vector"]])) + " result: " + str(lis[i]['label']) + "\n")

f.close()
