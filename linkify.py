from collections import defaultdict
import re
import word_map

CPRA = {
    'a': ['advertising and marketing'],
    'b': ['aggregate consumer information'],
    'c': ['biometric information'],
    'd': ['business', 'businesses'],
    'e': ['business purpose', 'business purposes'],
    'f': ['collect', 'collects', 'collected', 'collecting', 'collection'],
    'g': ['commercial purpose', 'commercial purposes'],
    'h': ['consent'],
    'i': ['consumer', 'consumers'],
    'j': ['contractor', 'contractors'],
    'k': ['cross-context behavioral advertising'],
    'l': ['dark pattern', 'dark patterns'],
    'm': ['deidentified'],
    'n': ['designated methods for submitting requests'],
    'o': ['device', 'devices'],
    'p': ['homepage'],
    'q': ['household', 'households'],
    'r': ['infer', 'infers', 'inferring', 'inference'],
    's': ['intentionally interact', 'intentionally interacts'],
    't': ['non-personalized advertising'],
    'u': ['person', 'persons'],
    'v': ['personal information'],
    'w': ['precise geolocation'],
    'x': ['probabilistic identifier', 'probabilistic identifiers'],
    'y': ['processing'],
    'z': ['profiling'],
    'aa': ['pseudonymize', 'pseudonymization'],
    'ab': ['research'],
    'ac': ['security and integrity'],
    'ad': ['sell', 'sells', 'selling', 'sale', 'sold'],
    'ae': ['sensitive personal information'],
    'af': ['service', 'services'],
    'ag': ['service provider', 'service providers'],
    'ah': ['share', 'shares', 'shared', 'sharing'],
    'ai': ['third party', 'third parties'],
    'aj': ['unique identifier', 'unique identifiers',
           'unique personal identifier', 'unique personal identifiers'],
    'ak': ['verifiable consumer request', 'verifiable consumer requests'],
}

CCPA = {
    'a': ['aggregate consumer information'],
    'b': ['biometric information'],
    'c': ['business', 'businesses'],
    'd': ['business purpose', 'business purposes'],
    'e': ['collect', 'collects', 'collected', 'collecting', 'collection'],
    'f': ['commercial purpose', 'commercial purposes'],
    'g': ['consumer', 'consumers'],
    'h': ['deidentified'],
    'i': ['designated methods for submitting requests'],
    'j': ['device', 'devices'],
    'k': ['health insurance information'],
    'l': ['homepage'],
    'm': ['infer', 'infers', 'inferring', 'inference'],
    'n': ['person', 'persons'],
    'o': ['personal information'],
    'p': ['probabilistic identifier', 'probabilistic identifiers'],
    'q': ['processing'],
    'r': ['pseudonymize', 'pseudonymization'],
    's': ['research'],
    't': ['sell', 'sells', 'selling', 'sale', 'sold'],
    'u': ['service', 'services'],
    'v': ['service provider', 'service providers'],
    'w': ['third party', 'third parties'],
    'x': ['unique identifier', 'unique identifiers',
           'unique personal identifier', 'unique personal identifiers'],
    'y': ['verifiable consumer request', 'verifiable consumer requests'],
}


def linkify(text, word_map, id_prefix=''):
    # build inverse map
    imap = {}
    for k, v in word_map.items():
        for w in v:
            imap[w] = k

    # substring lookup
    substrs = defaultdict(list)
    for w1 in imap.keys():
        for w2 in imap.keys():
            if w1 != w2 and w1 in w2:
                substrs[w1].append(w2)

    # this is DAG-ish. Want to make sure we don't linkify "personal" before
    # "personal information".
    for i in range(len(imap)):
        # pick a word that is not a substring
        word = list(set(imap) - set(substrs)).pop()

        # unblock words that are substrings of this one
        rm = []
        for k, v in substrs.items():
            if word in v:
                v.remove(word)
                if v:
                    substrs[k] = v
                else:
                    rm.append(k)  # can't modify the dict inline

        for k in rm:
            del substrs[k]

        # structure of markdown link
        pref = '['
        suf = '](#' + id_prefix + '1798.140(%s))' % imap[word]

        # create monster regex
        gex = re.compile('(?<!\w)' +    # non-word character preceding
                         word.replace(' ', '\s+') +     # the word itself
                         '(?!' + '([^\[]*\])' +     # negative lookahead for ]
                         '|\w)',        # and also non-word suffix
                         re.IGNORECASE)

        # loop until there are no more matches
        while True:
            m = gex.search(text)
            if not m:
                break
            end = m.end(0)
            start = m.start(0)
            text = text[:end] + suf + text[end:]
            text = text[:start] + pref + text[start:]

        del imap[word]

    return text
