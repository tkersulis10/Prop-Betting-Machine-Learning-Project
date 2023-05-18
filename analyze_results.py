import json
bins = []
went_over = 0
went_under = 0
bintot = 0
for i in range(0, 38):
    feature_vectors = open("svm_test_full5.txt", "r")
    for line in list(feature_vectors):
        json_obj = json.loads(line)
        label = float(json_obj["label"])
        # print(label)
        pred = float(json_obj["pred"])
        line = json_obj["lines"]
        if line == "none":
            continue
        if float(pred) != float(i):
            continue
        bintot += 1
        if label > pred:
            went_over += 1
        elif label < pred:
            went_under += 1
        else:
            bintot -= 1
        if bintot == 280:
            bintot = 0
            over_rate = went_over/(went_over+went_under)
            bins.append(over_rate - 0.5)
            went_over = 0
            went_under = 0
print(bins)

bins = []
went_over = 0
went_under = 0
bintot = 0
for i in range(0, 38):
    num = float(str(i)+".5")
    feature_vectors = open("svm_test_full5.txt", "r")
    for line in list(feature_vectors):
        json_obj = json.loads(line)
        label = float(json_obj["label"])
        # print(label)
        line = json_obj["lines"]
        if line == "none":
            continue
        line = float(json.loads(line)["consensus"][0].split("@")[0])
        if line != num:
            continue
        pred = line
        # print(pred)
        bintot += 1
        if label > pred:
            went_over += 1
        elif label < pred:
            went_under += 1
        else:
            bintot -= 1
        if bintot == 300:
            bintot = 0
            over_rate = went_over/(went_over+went_under)
            bins.append(over_rate - 0.5)
            went_over = 0
            went_under = 0
print(bins)


    # try:
    #     over_rate = went_over/(went_over+went_under)
    #     under_rate = went_under/(went_under+went_over)
    #     print(str(i) + ": " + str(over_rate) + " on volume " + str(went_over+went_under))
    # except:
    #     print(str(i) + ": zeros")
correct = 0
total = 0
unders = 0
overs = 0
went_over = 0
went_under = 0
feature_vectors = open("svm_test_full5.txt", "r")
for line in list(feature_vectors):
    json_obj = json.loads(line)
    label = json_obj["label"]
    line = json_obj["lines"]
    if line == "none":
        continue
    line = float(json.loads(line)["consensus"][0].split("@")[0])
    # line = 13.5



    pred = float(json_obj["pred"])
    # line = json_obj["feature_vector"][23]
    # pred = json_obj["feature_vector"][32]
    # line = float(json_obj["pred"])
    # pred = line
    # line = 1.5
    #90-97
    # avg = 0.0
    # for i in range(90, 98):
    #     avg += json_obj["feature_vector"][i]

    # pred = json_obj["feature_vector"][32]

    if label > pred:
        went_over += 1
    if label < pred:
        went_under += 1
    
    # line = json_obj["feature_vector"][32]
    if (pred < line):
        unders += 1
        if label < line:
            correct += 1
    elif pred > line:
        overs += 1
        if label > line:
            correct += 1
    else:
        total -= 1
    total += 1
print(correct)
print(total)
print(str(correct/total))
print(overs)
print(unders)
print(went_over)
print(went_under)