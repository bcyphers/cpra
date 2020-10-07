# load master markdown
with open('md/cpra.md') as f:
    md = f.read()

with open('md/cpra-both-head.md') as f:
    header = f.read()

with open('md/cpra-both.md', 'w') as f:
    f.write(header + '\n' + md)

# remove italic text
concat_it = md.replace('*\n\n*', '\n\n')
no_it = ''.join(concat_it.split('*')[::2])

with open('md/cpra-old-head.md') as f:
    header = f.read()

with open('md/cpra-old.md', 'w') as f:
    f.write(header + '\n' + no_it)

# remove strikethrough text
concat_st = md.replace('~~\n\n~~', '\n\n')
no_st = ''.join(concat_st.split('~~')[::2])

with open('md/cpra-new-head.md') as f:
    header = f.read()

with open('md/cpra-new.md', 'w') as f:
    f.write(header + '\n' + no_st)
