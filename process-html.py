import re
import sys

from bs4 import BeautifulSoup


LABEL_PAT = "\(\w+\.?\)"
COMPLEX_PAT = '\(<del>(\w+)<\/del><em>(\w+)<\/em>\)'
LINK_TMPL = '<a href="#%s">%s</a>'
CLASSES = ['section', 'sub1', 'sub2', 'sub3', 'sub4', 'sub5']


# given a label, figure out where we are in the structure of the law
def update_tree(tree, label):
    # levels: lowercase, numbers, uppercase, roman numerals, back to lowercase
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

    # if we get to here, the label is wonky
    raise NameError(label)


# create raw html for label link
def add_link(ptrn, p, pid, raw):
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
        sec_match = re.match('SEC(TION|\.)\s(\d+)', t)
        if sec_match:
            old_tree = []
            new_tree = []
            p['id'] = 'sec-' + sec_match.group(2)
            p['class'] = 'section-prop'
            continue

        # luckily, CPRA doesn't change any section titles
        title_match = re.match('(1798(\.\d+)+)\.?$', t)
        if title_match:
            name = title_match.group(1)

            old_tree = [name]
            new_tree = [name]
            p['id'] = name
            p['class'] = 'section-code'
            continue

        if not old_tree and not new_tree:
            # first entry in tree can only be a section header
            # therefore, if the tree is empty and we haven't matched a section
            # header, continue to the next iteration
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
                except NameError as e:
                    print('invalid label:', label)

                p = add_link(LABEL_PAT, p, name, raw)

                last_class = CLASSES[len(new_tree) - 1]
                p['class'] = last_class
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
                    p = add_link(LABEL_PAT, p, 'cpra-' + name, raw)

                elif strike and strike.text.startswith(label):
                    # if the label is contained inside the del element, the label is
                    # entirely old
                    old_tree, name = update_tree(old_tree, ltext)
                    last_class = CLASSES[len(old_tree) - 1]

                    # add link to label
                    p = add_link(LABEL_PAT, p, 'cpra-' + name, raw)

                elif raw.startswith(label):
                    # if the label is in raw text, it hasn't changed in the CPRA
                    # mark this as part of the CPRA's text, though it's
                    # technically part of both
                    old_tree, _ = update_tree(old_tree, ltext)
                    new_tree, name = update_tree(new_tree, ltext)
                    last_class = CLASSES[len(new_tree) - 1]

                    # add link to label
                    p = add_link(LABEL_PAT, p, 'cpra-' + name, raw)

                else:
                    # only other option is that this is a split label
                    raw_match = re.match(COMPLEX_PAT, raw)
                    l_old = raw_match.group(1)
                    l_new = raw_match.group(2)

                    old_tree, _ = update_tree(old_tree, l_old)
                    new_tree, name = update_tree(new_tree, l_new)
                    last_class = CLASSES[len(new_tree) - 1]

                    # add link to label
                    p = add_link(COMPLEX_PAT, p, 'cpra-' + name, raw)

            except NameError as e:
                print('invalid label:', label)


        # paragraphs without a heading get the same class as the one above
        p['class'] = last_class


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
