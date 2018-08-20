# RAVI: Resources Assignment and VIsualization #
* version 0.2

# Requires #
* Flask
* SQLAlchemy

# Installation

Setup a **virtualenv** containing Flask and SQLAlchemy:

```bash
virtualenv env --system-site-packages
. env/bin/activate
pip install Flask SQLAlchemy
```

# Running

```bash
 . env/bin/activate
 flask run
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
