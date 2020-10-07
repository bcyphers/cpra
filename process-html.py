import re
import sys

from bs4 import BeautifulSoup

def walk(soup):
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

        match = re.match('\(\w+\)', t)

        # we've matched a code section
        if match:
            label = match.group()
            label = label[1:-1]  # get rid of parens

            # levels:
            res = ['a?[a-z]+', '[0-9]+', '[A-Z]+', '(vi*)|(i+)|(iv)', 'NULL']
            for i in reversed(range(len(tree))):
                if re.match(res[i] + '$', label):
                    # shorten the tree, cutting off the deeper lists
                    tree = tree[:i+1]
                    # add the next element of the new list
                    tree.append(label)
                    id_text = tree[0] + ''.join(['(%s)' % i for i in tree[1:]])
                    p['id'] = id_text
                    break

        # paragraphs without a heading get the same class as the one above
        classes = ['section', 'sub1', 'sub2', 'sub3', 'sub4']
        p['class'] = classes[len(tree) - 1]


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
    walk(soup)

    # replace em and del with spans
    replace_with_spans(soup)

    # add style
    style = BeautifulSoup(
        '<link rel="stylesheet" href="/cpra/style.css" type="text/css">',
        features='html.parser')
    soup.head.insert(0, style)

    with open(sys.argv[2], 'w') as f:
        f.write(str(soup))
