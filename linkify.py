from collections import defaultdict
import word_map

with open('md/cpra.md') as f:
    text = f.read().replace('\n', ' ')

wmap = {}
for k, v in word_map.cpra.items():
    for w in v:
        wmap[w] = k


substrs = defaultdict(list)
for w1 in wmap.keys():
    for w2 in in wmap.keys():
        if w1 != w2 and w1 in w2:
            substrs[w1].append(w2)


for i in range(len(wmap)):
    # pick a word that is not a substring
    word = list(set(wmap) - set(substrs)).pop()

    # unblock words that are substrings of this one
    for k, v in substrs.items():
        if word in v:
            v.remove(word)
            if v:
                substrs[k] = v
            else:
                del substrs[k]

    # linkify
    link = '[%s](#1798.140(%s))' % (word, wmap[word])
    gex = re.compile('^\[' + re.escape(word), re.IGNORECASE)
    text = gex.sub(link, text)

print text
