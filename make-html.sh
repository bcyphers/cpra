python make-md.py

pandoc -s md/both.md -t html -o html/both.html --metadata pagetitle='CPRA'
pandoc -s md/new.md -t html -o html/new.html --metadata pagetitle='CPRA'
pandoc -s md/old.md -t html -o html/old.html --metadata pagetitle='CPRA'

python process-html.py html/both.html www/index.html 1
python process-html.py html/new.html www/new.html 0
python process-html.py html/old.html www/old.html 0
