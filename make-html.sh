python make-md.py

pandoc -s md/cpra-both.md -t html -o html/cpra-both.html --metadata pagetitle='CPRA'
pandoc -s md/cpra-new.md -t html -o html/cpra-new.html --metadata pagetitle='CPRA'
pandoc -s md/cpra-old.md -t html -o html/cpra-old.html --metadata pagetitle='CPRA'

#python process-html.py html/cpra-both.html out/both.html
python process-html.py html/cpra-new.html out/new.html
#python process-html.py html/cpra-old.html out/old.html
