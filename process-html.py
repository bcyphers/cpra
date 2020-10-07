import re
import sys

from bs4 import BeautifulSoup


label_pat = "\(\w+\.?\)"
classes = ['section', 'sub1', 'sub2', 'sub3', 'sub4', 'sub5']


def update_tree(tree, label):
    # levels: lowercase, numbers, uppercase, roman numerals
    res = ['a?[a-z]+', '[0-9]+', '[A-Z]+', '(vi*)|(i+)|(iv)', "[a-z]\.", 'NULL']
    for i in reversed(range(len(tree))):
        if re.match(res[i] + '$', label):
            # shorten the tree, cutting off the deeper lists
            tree = tree[:i+1]
            # add the next element of the new list
            tree.append(label)
            # create the id text
            id_text = tree[0] + ''.join(['(%s)' % i for i in tree[1:]])

            # we're done
            return tree, id_text

    raise NameError(label)


def walk_easy(soup):
    paras = soup.find_all('p')
    tree = []
    for p in paras:
        # TODO
        # if there is both a strikethrough and an italic, handle it

        t = p.text
        sec_match = re.match('(1798(\.\d+)+)\.?$', t)
        if sec_match:
            tree = [sec_match.group(1)]
            id_text = tree[0]
            p['id'] = id_text
            p['class'] = 'section-code'
            continue

        if re.match('SEC(TION|\.)\s\d+', t):
            tree = []
            p['class'] = 'section-bal'
            continue

        if len(tree) == 0:
            # first entry in tree can only be a section header
            # therefore, if the tree is empty and we haven't matched a section
            # header, continue to the next iter
            continue

        match = re.match(label_pat, t)

        # we've matched a code section
        if match:
            label = match.group()
            label = label[1:-1]  # get rid of parens
            try:
                tree, id_text = update_tree(tree, label)
                p['id'] = id_text
            except NameError as e:
                print('invalid label:', label)

        # paragraphs without a heading get the same class as the one above
        p['class'] = classes[len(tree) - 1]


def walk_hard(soup):
    paras = soup.find_all('p')
    old_tree = []
    new_tree = []
    last_class = ''

    for p in paras:
        t = p.text

        # these are sections of CPRA, not sections of code
        if re.match('SEC(TION|\.)\s\d+', t):
            old_tree = []
            new_tree = []
            p['class'] = 'section-bal'
            continue

        # luckily, CPRA doesn't change any section titles
        sec_match = re.match('(1798(\.\d+)+)\.?$', t)
        if sec_match:
            id_text = sec_match.group(1)

            old_tree = [id_text]
            new_tree = [id_text]
            p['id'] = id_text
            p['class'] = 'section-code'
            continue

        if not old_tree and not new_tree:
            # first entry in tree can only be a section header
            # therefore, if the tree is empty and we haven't matched a section
            # header, continue to the next iter
            continue

        match = re.match(label_pat, t)

        # we've matched a code section
        if match:
            # if there is both a strikethrough and an italic, handle it.
            # there are only a couple of possibilities:
            # 1. the label is all plain, all italic, or all strikethrough from
            #   paren to paren.
            # 2. the left and right parens are plain, and there are two
            #   different labels inside. First one is strikethrough, and second
            #   one is italic.

            label = match.group()
            ltext = label[1:-1]

            # look for the label inside italics and strikethroughs
            # luckily, the ones we care about will always be the first elements
            italic = p.find('em')
            strike = p.find('del')
            raw = p.decode_contents()

            try:
                if italic and italic.text.startswith(label):
                    # if the label is contained inside the em element, the label is
                    # entirely new
                    new_tree, name = update_tree(new_tree, ltext)
                    p['id'] = 'cpra-' + name
                    last_class = classes[len(new_tree) - 1]

                elif strike and strike.text.startswith(label):
                    # if the label is contained inside the del element, the label is
                    # entirely old
                    old_tree, name = update_tree(old_tree, ltext)
                    p['id'] = 'ccpa-' + name
                    last_class = classes[len(old_tree) - 1]

                elif raw.startswith(label):
                    # if the label is in raw text, it hasn't changed in the CPRA
                    # mark this as part of the CPRA's text, though it's
                    # technically part of both
                    old_tree, _ = update_tree(old_tree, ltext)
                    new_tree, name = update_tree(new_tree, ltext)
                    p['id'] = 'cpra-' + name
                    last_class = classes[len(new_tree) - 1]

                else:
                    # only other option is that this is a split label
                    raw_match = re.match('\(<del>(\w+)<\/del><em>(\w+)<\/em>\)', raw)
                    l_old = raw_match.group(1)
                    l_new = raw_match.group(2)

                    old_tree, _ = update_tree(old_tree, l_old)
                    new_tree, name = update_tree(new_tree, l_new)
                    p['id'] = 'cpra-' + name
                    last_class = classes[len(new_tree) - 1]

            except NameError as e:
                print('invalid label:', label)


        # paragraphs without a heading get the same class as the one above
        p['class'] = last_class


def replace_with_spans(soup):
    # replace `em` italics with spans
    for node in soup.find_all('em'):
        replacement = soup.new_tag('span', **{'class':'new-text'})
        replacement.string = node.string
        node.replace_with(replacement)

    # replace `del` strikethroughs with spans
    for node in soup.find_all('del'):
        replacement = soup.new_tag('span', **{'class':'old-text'})
        replacement.string = node.string
        node.replace_with(replacement)


if __name__ == '__main__':
    with open(sys.argv[1]) as f:
        soup = BeautifulSoup(f.read(), features='html.parser')

    # annotate text
    if sys.argv[3] == '1':
        walk_hard(soup)
    else:
        walk_easy(soup)

    # replace em and del with spans
    replace_with_spans(soup)

    # add style
    style = BeautifulSoup(
        '<link rel="stylesheet" href="/cpra/style.css" type="text/css">',
        features='html.parser')
    soup.head.insert(0, style)

    with open(sys.argv[2], 'w') as f:
        f.write(str(soup))
