import linkify

# load master markdown
with open('md/cpra.md') as f:
    md = f.read()

# remove italic text
concat_it = md.replace('*\n\n*', '\n\n')
no_it = ''.join(concat_it.split('*')[::2])

# remove strikethrough text
concat_st = md.replace('~~\n\n~~', '\n\n')
no_st = ''.join(concat_st.split('~~')[::2])

# create 'both' page
link_md = linkify.linkify(md, linkify.CPRA, id_prefix='cpra-')
with open('md/cpra-both-head.md') as f:
    header = f.read()

with open('md/cpra-both.md', 'w') as f:
    f.write(header + '\n' + link_md)

# create 'old' page
link_it = linkify.linkify(no_it, linkify.CCPA)
with open('md/cpra-old-head.md') as f:
    header = f.read()

with open('md/cpra-old.md', 'w') as f:
    f.write(header + '\n' + link_it)

# create 'new' page
link_st = linkify.linkify(no_st, linkify.CPRA)
with open('md/cpra-new-head.md') as f:
    header = f.read()

with open('md/cpra-new.md', 'w') as f:
    f.write(header + '\n' + link_st)
