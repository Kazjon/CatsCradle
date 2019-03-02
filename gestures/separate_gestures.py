
import pandas as pd
import re

INCLUDE_REVERSE = False

with open('sequences.csv', 'r') as f:
    contents = f.read()

emotions = ['SAD', 'SHAME', 'FEAR', 'SURPRISE', 'LONGING', 'NEUTRAL GESTURES']
parts_pattern = re.compile('|'.join(emotions))
parts = re.split(parts_pattern, contents)

seq_pattern = re.compile('number ([^\t\n\r\f\v]*)\n([^\t\n\r\f\v]*)\n')

sequences = {}
for counter, e in enumerate(emotions, 1):
    sequences[e] = {}
    seqs = re.findall(seq_pattern, parts[counter])
    for s in seqs:
        sequences[e][s[0]] = s[1].strip(',').strip(' ').split(',')

for em, val in sequences.iteritems():
    contents = []
    id_counter = 1
    contents.append('ID,Name,Sequence')
    for seq_key, seq in sorted(val.iteritems(), key=lambda (k,v): (v,k)):
	seq_without_sp = []
	for s in seq:
	    if s == '':
		continue
	    seq_without_sp.append(s.strip(' '))
        if INCLUDE_REVERSE or (not INCLUDE_REVERSE and not "reverse" in seq_key):
            weight = 1
            if '*' in seq_key:
                weight = 2
            content = str(id_counter) + ',' + str(weight) + ',' + ','.join(seq_without_sp)
        else:
            continue
        contents.append(content)
        id_counter += 1
    contents_str = '\n'.join(contents)
    with open(str(em.split(' ')[0]).lower() + '_gestures.csv', 'w') as f:
        f.write(contents_str)

