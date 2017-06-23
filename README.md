# RAVI: Resources Assignment and VIsualization #
* version 0.1

# Requires #
* Flask
* SQLAlchemy
* Plotly
* Matplotlib (Only for generating the project plots offline)

# Installation
First install miniconda
```
git clone https://ridderlars@bitbucket.org/ridderlars/ravi.git
cd ravi
wget -P js https://cdn.plot.ly/plotly-latest.min.js
conda create -n ravi
source activate ravi
conda install matplotlib
conda install pandas
python setup.py develop
```

# Running Ravi
First start the server:
```
source activate ravi
ravi database.db exported_hours_from_exact.csv
```
then open index.html in browser

# Generating all project plots offline (planned vs written hours)
```
source activate ravi
ravi database.db exported_hours_from_exact.csv output_folder
```

# Exporting hours from Exact
* Go to "Projecten" => "Tijd- en kosteninvoer" => "Ingevoerde tijd en kosten"
* Select tab "Exporteerbaar"
* Make sure the following columns are included (add if necessary by the option "aanpassen" in the top-right menu):
    * Projectcode
    * Medewerker ID
    * Datum
    * Aantal
    * Uur- of kostensoort (Code)
* Choose "Exporteren: Excel" in the top-right menu
* In Excel: Remove the top 13 or so lines to keep only one header line and data
* Save as CSV, using "," as field delimiter and no text delimiter


# Contact #
* l.ridder@esciencecenter.nl
