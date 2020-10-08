import re
import sys
import string

from bs4 import BeautifulSoup


SEC_PAT = 'SEC(TION|\.)\s(\d+)\.'
TITLE_PAT = '(1798(\.\d+)+)\.?'
LABEL_PAT = "\(\w+\.?\)"
TAG_PAT = "\((\<\w+\>)?\w+\.?(\<\/\w+\>)?\)"
COMPLEX_PAT = '\(<del>(\w+)<\/del><em>(\w+)<\/em>\)'
LINK_TMPL = '<a href="#%s" class="para-label">%s</a>'
CLASSES = ['section', 'sub1', 'sub2', 'sub3', 'sub4', 'sub5']


# is this elegant? no. is it necessary? also no
def to_roman(n):
    nums = [(10, 'x'), (9, 'ix'), (5, 'v'), (4, 'iv'), (1, 'i')]
    res = ''
    for val, num in nums:
        res += num * (n // val)
        n = n % val

    return res


INDENT_LEVELS = [
    # lowercase letters
    list(string.ascii_lowercase) +
        ['a' + l for l in string.ascii_lowercase],
    # arabic numerals
    map(str, range(1, 100)),
    # uppercase letters
    list(string.ascii_uppercase) +
        ['A' + l for l in string.ascii_uppercase],
    # lowercase roman numerals
    map(to_roman, range(1, 20)),
    # uppercase roman numerals
    map(lambda i: to_roman(i).upper(), range(1, 20))
]


# given a label, figure out where we are in the structure of the law
def update_tree(tree, label):
    # first check for the next deepest level
    if (len(tree) <= len(INDENT_LEVELS) and
        label == INDENT_LEVELS[len(tree) - 1][0]):
        tree.append(label)
    else:
        # now check for the next value in sequence for one of the levels we've
        # already reached
        for i in reversed(range(1, len(tree))):
            lvl = INDENT_LEVELS[i-1]

            # find out where in the sequence we are
            if (tree[i] in lvl and
                label == lvl[lvl.index(tree[i]) + 1]):
                # concat the tree and add the label to the end
                tree = tree[:i] + [label]
                break
        else:
            # if we get to here, the label is wonky
            raise NameError('.'.join(tree + [label]))

    # create the id text
    id_text = tree[0] + ''.join(['(%s)' % i for i in tree[1:]])

    # we're done
    return tree, id_text


# create raw html for label link
# ptrn: pattern to match. must match whole section to be linked.
# p: paragraph bs4 object to modify
# pid: the ID of the paragraph
def add_link(ptrn, p, pid):
    raw = p.decode_contents()
    new_html = re.sub(ptrn,
                      lambda m: LINK_TMPL % (pid, m.group(0)),
                      raw,
                      count=1)

    # add it to beautifulsoup object (why is this so difficult?)
    new_node = BeautifulSoup(new_html, features='html.parser')
    new_p = soup.new_tag('p', **{'id': pid})
    for i in range(len(new_node.contents)):
        new_p.append(new_node.contents[0].extract())
    p.replace_with(new_p)

    return new_p


# walk through the DOM and add IDs to the paragraphs
def walk(soup, simple=True):
    paras = soup.find_all('p')
    old_tree = []
    new_tree = []
    last_class = ''

    for p in paras:
        t = p.text

        # these are sections of CPRA, not sections of code
        sec_match = re.match(SEC_PAT, t)
        if sec_match:
            old_tree = []
            new_tree = []

            name = 'sec-' + sec_match.group(2)
            p = add_link(SEC_PAT, p, name)
            p['class'] = 'section-prop'

            continue

        # luckily, CPRA doesn't change any section titles
        title_match = re.match(TITLE_PAT, t)
        if title_match:
            name = title_match.group(1)
            old_tree = [name]
            new_tree = [name]

            p = add_link(TITLE_PAT, p, name)
            p['class'] = 'section-code'

            continue

        # first entry in tree can only be a section header
        # therefore, if the tree is empty and we haven't matched a section
        # header, continue to the next iteration
        if not old_tree and not new_tree:
            continue

        match = re.match(LABEL_PAT, t)

        # we've matched a code section
        if match:
            label = match.group()
            ltext = label[1:-1]  # what's inside the parens
            raw = p.decode_contents()

            # if we don't have to differentiate between two styles of label, we
            # don't care about the formatting.
            if simple:
                try:
                    new_tree, name = update_tree(new_tree, ltext)
                    p = add_link(TAG_PAT, p, name)
                    last_class = CLASSES[len(new_tree) - 1]
                except NameError as e:
                    print('invalid label:', e)
                    p['class'] = 'invalid'

                p['class'] = p.get('class', '') + ' ' + last_class
                continue

            # if there is both a strikethrough and an italic, handle it.
            # there are only a couple of possibilities:
            # 1. the label is all plain, all italic, or all strikethrough from
            #   paren to paren.
            # 2. the left and right parens are plain, and there are two
            #   different labels inside. First one is strikethrough, and second
            #   one is italic.
            #
            # look for the label inside italics and strikethroughs
            # luckily, the ones we care about will always be the first elements
            italic = p.find('em')
            strike = p.find('del')

            try:
                if italic and italic.text.startswith(label):
                    # if the label is contained inside the em element, the label is
                    # entirely new
                    new_tree, name = update_tree(new_tree, ltext)
                    last_class = CLASSES[len(new_tree) - 1]

                    # add link to label
                    p = add_link(LABEL_PAT, p, 'cpra-' + name)

                elif strike and strike.text.startswith(label):
                    # if the label is contained inside the del element, the label is
                    # entirely old
                    old_tree, name = update_tree(old_tree, ltext)
                    last_class = CLASSES[len(old_tree) - 1]

                    # add link to label
                    p = add_link(LABEL_PAT, p, 'ccpa-' + name)

                elif raw.startswith(label):
                    # if the label is in raw text, it hasn't changed in the CPRA
                    # mark this as part of the CPRA's text, though it's
                    # technically part of both
                    old_tree, _ = update_tree(old_tree, ltext)
                    new_tree, name = update_tree(new_tree, ltext)
                    last_class = CLASSES[len(new_tree) - 1]

                    # add link to label
                    p = add_link(LABEL_PAT, p, 'cpra-' + name)

                else:
                    # only other option is that this is a split label
                    raw_match = re.match(COMPLEX_PAT, raw)
                    l_old = raw_match.group(1)
                    l_new = raw_match.group(2)

                    old_tree, _ = update_tree(old_tree, l_old)
                    new_tree, name = update_tree(new_tree, l_new)
                    last_class = CLASSES[len(new_tree) - 1]

                    # add link to label
                    p = add_link(COMPLEX_PAT, p, 'cpra-' + name)

            except NameError as e:
                print('invalid label:', e)


        # paragraphs without a heading get the same class as the one above
        p['class'] = p.get('class', '') + ' ' + last_class


# the html is filled with <em> and <del> elements; we want to replace those with
# <spans> with classes for easier styling.
def replace_with_spans(soup):
    # replace `em` italics with spans
    for node in soup.find_all('em'):
        replacement = soup.new_tag('span', **{'class':'new-text'})
        for i in range(len(node.contents)):
            n = node.contents[0].extract()  # pop off the front
            replacement.append(n)
        node.replace_with(replacement)

    # replace `del` strikethroughs with spans
    for node in soup.find_all('del'):
        replacement = soup.new_tag('span', **{'class':'old-text'})
        for i in range(len(node.contents)):
            n = node.contents[0].extract()  # pop off the front
            replacement.append(n)
        node.replace_with(replacement)


if __name__ == '__main__':
    with open(sys.argv[1]) as f:
        soup = BeautifulSoup(f.read(), features='html.parser')

    # annotate text
    if sys.argv[3] == '1':
        walk(soup, simple=False)
    else:
        walk(soup, simple=True)

    # replace em and del with spans
    replace_with_spans(soup)

    # add style
    style = BeautifulSoup(
        '<link rel="stylesheet" href="/cpra/style.css" type="text/css">',
        features='html.parser')
    soup.head.insert(0, style)

    with open(sys.argv[2], 'w') as f:
        f.write(str(soup))
