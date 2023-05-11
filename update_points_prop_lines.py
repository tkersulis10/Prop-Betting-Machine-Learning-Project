import json

points_prop_lines = open("points_prop_lines.txt", "r")
for line in points_prop_lines:
    if "Player" in line:
        valid = True
        j = json.loads(line)
        lines = json.loads(j["lines"])
        consensus = lines["consensus"]
        over = consensus[0].split("@")
        if (float(over[0]) < 4.5):
            print(line)
            continue
        if (int(over[1]) < -150):
            print(line)
            continue
        under = consensus[1].split("@")
        if (float(under[0]) < 4.5):
            print(line)
            continue
        if (int(under[1]) < -150):
            print(line)
            continue
        f = open("points_prop_lines2.txt", "a")
        f.write(line)
        f.close()
    else:
        f = open("points_prop_lines2.txt", "a")
        f.write(line)
        f.close()