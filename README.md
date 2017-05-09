# RAVI: Resources Assignment and VIsualization #
* version 0.1

# Requires #
* Flask
* SQLAlchemy
* Plotly

# Installation
```
git clone https://ridderlars@bitbucket.org/ridderlars/ravi.git
cd ravi
wget -P js https://cdn.plot.ly/plotly-latest.min.js
virtualenv ravi
source ravi/bin/activate
python setup.py install
```

# Running Ravi
```
source ravi/bin/activate
ravi database.db dump_from_exact.csv
```
then open ravi/index.html in browser

# Exporting data from Exact
- Go to Projecten=>Tijd- en kosteninvoer=>Ingevoerde tijd en kosten
- Select tab "Exporteerbaar"
- Make sure the following columns are included:
- Projectcode
-- 


# Contact #
* l.ridder@escienecenter.nl