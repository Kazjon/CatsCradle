import pandas as pd


with open('interactions.log', 'rt') as f:
    logs = f.readlines()

# remove empty lines
logs = [l for l in logs if l != '']

print("len(logs)=" + str(len(logs)) + "\n")

#######

rules = []
counts = {'shame': 0, 'fear': 0, 'longing': 0, 'surprise': 0, 'neutral': 0}
for log in logs:
    if 'RULES' in log:
        r = log.split(':')[3][:-1]
        rules.append(r)
    if 'EMOTION:surprise' in log:
        counts['surprise'] += 1
    if 'EMOTION:fear' in log:
        counts['fear'] += 1
    if 'EMOTION:longing' in log:
        counts['longing'] += 1
    if 'EMOTION:shame' in log:
        counts['shame'] += 1
    if 'EMOTION:NEUTRAL' in log:
        counts['neutral'] += 1

print("len(neutral)=" + str(counts['neutral']))
print("len(shame)=" + str(counts['shame']))
print("len(longing)=" + str(counts['longing']))
print("len(fear)=" + str(counts['fear']))
print("len(surprise)=" + str(counts['surprise']))
print("\nlen(rules)=" + str(len(rules)) + "\n")

r_str = ','.join(rules)
r_arr = r_str.split(',')
r_series = pd.Series(r_arr)

print(str(r_series.value_counts()))

#######
