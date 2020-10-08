#python make-md.py

echo "Converting markdown to html..."
pandoc -s md/both.md -t html -o html/both.html --metadata pagetitle='CPRA'
pandoc -s md/new.md -t html -o html/new.html --metadata pagetitle='CPRA'
pandoc -s md/old.md -t html -o html/old.html --metadata pagetitle='CPRA'

echo "Labeling redline page..."
python process-html.py html/both.html www/index.html 1
echo "Labeling CCPA page..."
python process-html.py html/old.html www/old.html 0
echo "Labeling clean CPRA page..."
python process-html.py html/new.html www/new.html 0
