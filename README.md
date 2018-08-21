# RAVI: Resources Assignment and VIsualization #
* version 0.2

This is a tool to help planning the assignment of people to projects.
There are many tools like it, but this is our tool ;)

Our specific version of the planning problem is:
 * on the order of 50 projects and 50 engineers
 * projects run typically between 6 months and 4 years
 * accounting is based on hours, projects require between 1 and 4 FTE of work
 * we plan with monthly precision
 * 1 or 2 engineers plus a coordinator work on a project at the same time
 * an engineer works on 1 to 5 projects
 * an engineer can work parttime
 * cross comparison with actually worked hours, as registered in a separate system is required

# Requires #
* Flask
* SQLAlchemy

# Installation

Setup a **virtualenv** containing Flask and SQLAlchemy:

```bash
virtualenv env --system-site-packages
. env/bin/activate
pip -r requirements.txt
```

Setup a sqlite3 database with the necessary tables:
```bash
sqlite3 database.db
sqlite> .read SCHEMA.sql
sqlite> .quit
```

# Running

```bash
 . env/bin/activate
 flask run
```

# Documentation

See *README.tables* for a description of the main database tables.
See *README.exact* on how to import written hours into the database.
See *README.triggers* on a description of the audit log.

User interface documentation: TODO

# Contact #
* l.ridder@esciencecenter.nl
* j.attema@esciencecenter.nl
