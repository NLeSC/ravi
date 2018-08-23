"""
Resources Assignment and VIewing (RAVI) tool
"""

from flask import Flask, Response, json, request, abort, redirect
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from items import Base, Engineer, Project, Assignment
import sys
import datetime
from builtins import str

PROJECT_AND_FTES = "SELECT * FROM (SELECT pid, fte, start, end, coordinator, comments, exact_code, active FROM projects ORDER BY pid) LEFT OUTER JOIN (SELECT pid, SUM(assignments.fte * (assignments.end - assignments.start)) / 12 AS assigned FROM assignments GROUP BY pid) USING (pid)"

REQUIRED_FTE="WITH boundaries AS ( SELECT start AS 'edge' FROM projects UNION SELECT end AS 'edge' FROM projects ORDER BY edge), intervals AS ( SELECT b1.edge AS start, b2.edge AS end FROM boundaries b1 JOIN boundaries b2 ON b2.edge = (SELECT MIN(edge) FROM boundaries b3 WHERE b3.edge > b1.edge)) SELECT intervals.start AS start, intervals.end AS end, sum(projects.fte * 12 / (projects.end - projects.start)) AS fte, intervals.end - intervals.start AS months FROM projects, intervals WHERE projects.start < intervals.end AND projects.end > intervals.start GROUP BY intervals.start, intervals.end"

AVAILABLE_FTE="WITH boundaries AS ( SELECT start AS 'edge' FROM assignments WHERE assignments.eid NOT LIKE '00_%' UNION SELECT end AS 'edge' FROM assignments WHERE assignments.eid NOT LIKE '00_%' ORDER BY edge), intervals AS ( SELECT b1.edge AS start, b2.edge AS end FROM boundaries b1 JOIN boundaries b2 ON b2.edge = (SELECT MIN(edge) FROM boundaries b3 WHERE b3.edge > b1.edge)) SELECT intervals.start AS start, intervals.end AS end, sum(assignments.fte) AS fte, intervals.end - intervals.start AS months FROM assignments, intervals WHERE assignments.start < intervals.end AND assignments.end > intervals.start AND assignments.eid NOT LIKE '00_%' GROUP BY intervals.start, intervals.end ORDER BY intervals.start"

ENGINEER_LOAD = "WITH boundaries AS ( SELECT eid, end AS 'edge' FROM assignments UNION SELECT eid, start AS 'edge' FROM assignments UNION SELECT eid, start AS 'edge' FROM engineers UNION SELECT eid, end AS 'edge' FROM engineers ORDER BY eid, edge), intervals AS ( SELECT b1.eid AS eid, b1.edge AS start, b2.edge AS end FROM boundaries b1 JOIN boundaries b2 ON b1.eid = b2.eid AND b2.edge = (SELECT MIN(edge) FROM boundaries b3 WHERE b3.edge > b1.edge AND b3.eid = b2.eid)), load AS ( SELECT intervals.eid AS eid, intervals.start AS start, intervals.end AS end, sum(assignments.fte) AS fte FROM assignments, intervals WHERE assignments.eid = intervals.eid AND assignments.start < intervals.end AND assignments.end > intervals.start GROUP BY intervals.eid, intervals.start, intervals.end) SELECT load.eid AS eid, load.start AS start, load.end AS end, load.fte - engineers.fte AS fte FROM load, engineers WHERE load.eid = engineers.eid"

ENGINEERS="SELECT * FROM ( SELECT engineers.eid AS eid, engineers.start AS start, engineers.end AS end, engineers.fte AS fte, engineers.exact_id AS exact_id, engineers.coordinator AS coordinator, engineers.comments AS comments, engineers.active AS active FROM engineers ORDER BY engineers.eid ) LEFT OUTER JOIN ( WITH edges AS (SELECT (strftime('%Y', date('now')) * 12 + strftime('%m', date('now')) - 1) AS start, (strftime('%Y', date('now')) * 12 + strftime('%m', date('now')) - 1 + 3) AS end) SELECT engineers.eid AS eid, sum(min(max(assignments.end - edges.start, edges.end - assignments.start, 0), assignments.end - assignments.start, edges.end - edges.start) * assignments.fte) / 3 AS assigned, engineers.fte AS available FROM edges, assignments, engineers WHERE edges.start < assignments.end AND edges.end > assignments.start AND assignments.eid = engineers.eid GROUP BY engineers.eid ) USING (eid)"

app = Flask(__name__)

def ym2date(ym):
    if ym:
        y, m = divmod(ym, 12)
        return "{:4d}-{:02d}".format(y, m+1)
    else:
        return None

def date2ym(date):
    if date:
        d = date.split('-')
        return 12 * int(d[0]) + int(d[1]) - 1
    else:
        return None

def flask_response(data):
    resp = Response(json.dumps(data), mimetype='application/json')
    resp.headers['Access-Control-Allow-Origin'] = '*'
    return resp

@app.errorhandler(500)
def custom500(error):
    resp = Response(json.dumps({'error': error.description}), 500, mimetype='application/json')
    resp.headers['Access-Control-Allow-Origin'] = '*'
    return resp

@app.route('/get_engineers', methods = ['GET'])
def get_engineers():
    my_query = text(ENGINEERS)
    data = []
    for e in engine.execute(my_query):
        d = dict(e)
        d['start'] = ym2date(d['start'])
        d['end'] = ym2date(d['end'])
        data.append(d)
    return flask_response(data)

@app.route('/get_log', methods = ['POST'])
def get_log():
    queryText = "SELECT * FROM AUDIT WHERE 1 "

    filterBy = json.loads(request.get_data())
    if filterBy['project'] != "all":
        queryText += " AND (oldpid = '" + filterBy['project'] +"' OR newpid = '" + filterBy['project'] +"')"
    if filterBy['engineer'] != "all":
        queryText += " AND (oldeid = '" + filterBy['engineer'] +"' OR neweid = '" + filterBy['engineer'] +"')"
    queryText += "ORDER BY date DESC LIMIT 25"

    my_query = text(queryText)
    data = []
    for e in engine.execute(my_query):
        d = dict(e)
        d['oldstart'] = ym2date(d['oldstart'])
        d['newstart'] = ym2date(d['newstart'])
        d['oldend'] = ym2date(d['oldend'])
        d['newend'] = ym2date(d['newend'])
        data.append(d)
    return flask_response(data)

@app.route('/get_project_written_hours', methods = ['POST'])
def get_project_written_hours():
    project_data = json.loads(request.get_data())
    my_query = text("SELECT Medewerker, SUM(Aantal) AS Aantal, Year, Month FROM hours WHERE Projectcode = '" + project_data['Projectcode'] + "' GROUP BY Medewerker, Year, Month ORDER BY Year, Month, Medewerker")
    data = []
    for e in engine.execute(my_query):
        d = dict(e)
        d['date'] = "{:4d}-{:d}".format(d['Year'], d['Month'])
        data.append(d)
    return flask_response(data)

@app.route('/get_engineer_load', methods = ['GET'])
def get_engineer_load():
    my_query = text(ENGINEER_LOAD)
    data = []
    for e in engine.execute(my_query):
        d = dict(e)
        d['start'] = ym2date(d['start'])
        d['end'] = ym2date(d['end'])
        data.append(d)
    return flask_response(data)

@app.route('/get_overview', methods = ['GET'])
def get_overview():
    my_query = text(REQUIRED_FTE)
    req = []
    for e in engine.execute(my_query):
        d = dict(e)
        d['start'] = ym2date(d['start'])
        d['end'] = ym2date(d['end'])
        req.append(d)

    my_query = text(AVAILABLE_FTE)
    avl = []
    for e in engine.execute(my_query):
        d = dict(e)
        d['start'] = ym2date(d['start'])
        d['end'] = ym2date(d['end'])
        avl.append(d)

    data = dict()
    data['required'] = req
    data['available'] = avl
    return flask_response(data)

@app.route('/get_projects', methods = ['GET'])
def get_projects():
    my_query = text(PROJECT_AND_FTES)
    data = []
    for p in engine.execute(my_query):
        d = dict(p)
        d['start'] = ym2date(d['start'])
        d['end'] = ym2date(d['end'])
        data.append(d)
    return flask_response(data)

@app.route('/update_engineer', methods = ['POST'])
def update_engineer():
    try:
        session.query(Engineer).filter_by(eid=str(request.form['eid'])).update({
            'eid': str(request.form['eid']),
            'fte': str(request.form['fte']),
            'start': date2ym(str(request.form['start'])),
            'end': date2ym(str(request.form['end'])),
            'coordinator': str(request.form['coordinator']),
            'active': int(request.form['active'])
            })
    except Exception as err:
        abort(500, "Parsing engineer failed:\n\n" + str(err))

    try:
        session.commit()
    except Exception as err:
        session.rollback()
        abort(500, "Updating assignment failed:\n\n" + str(err))

    return flask_response(["success"])

@app.route('/update_project', methods = ['POST'])
def update_project():
    try:
        session.query(Project).filter_by(pid=str(request.form['pid'])).update({
            'pid': str(request.form['pid']),
            'fte': str(request.form['fte']),
            'start': date2ym(str(request.form['start'])),
            'end': date2ym(str(request.form['end'])),
            'coordinator': str(request.form['coordinator']),
            'active': int(request.form['active'])
            })
    except Exception as err:
        abort(500, "Parsing project failed:\n\n" + str(err))

    try:
        session.commit()
    except Exception as err:
        session.rollback()
        abort(500, "Updating assignment failed:\n\n" + str(err))

    return flask_response(["success"])

@app.route('/get_assignments', methods = ['POST'])
def get_assignments():
    my_query = "SELECT aid, pid, eid, start, end, fte FROM assignments "
    if (len(request.form['pid']) > 0 and len(request.form['eid']) > 0):
        my_query += "WHERE pid = '" + request.form['pid'] + "' AND eid = '" + request.form['eid'] + "' "
    elif (len(request.form['pid']) > 0):
        my_query += "WHERE pid = '" + request.form['pid'] + "' "
    elif (len(request.form['eid']) > 0):
        my_query += "WHERE eid = '" + request.form['eid'] + "' "
    my_query += "ORDER BY pid, eid, start"

    data = []
    for a in engine.execute(my_query):
        d = dict(a)
        d['start'] = ym2date(d['start'])
        d['end'] = ym2date(d['end'])
        data.append(d)
    return flask_response(data)
  
@app.route('/add_assignment', methods = ['POST'])
def add_assignment():
    # Create and add the assignment to the database
    assignment = Assignment()
    assignment.eid = str(request.form['eid'])
    assignment.pid = str(request.form['pid'])
    assignment.fte = str(request.form['fte'])
    assignment.start = date2ym(str(request.form['start']))
    assignment.end = date2ym(str(request.form['end']))
    session.add(assignment)

    try:
        session.commit()
    except Exception as err:
        session.rollback()
        abort(500, "Adding assignment failed:\n\n" + str(err))

    # Now that the assignment has been added, it has an unique 'eid'
    # So respond with the full assignment
    d = dict()
    d['aid'] = assignment.aid
    d['eid'] = assignment.eid
    d['pid'] = assignment.pid
    d['fte'] = assignment.fte
    d['start'] = ym2date(assignment.start)
    d['end'] = ym2date(assignment.end)

    return flask_response(d)

@app.route('/update_assignment', methods = ['POST'])
def update_assignment():
    try:
        session.query(Assignment).filter_by(aid=int(request.form['aid'])).update({
            'eid': str(request.form['eid']),
            'pid': str(request.form['pid']),
            'fte': str(request.form['fte']),
            'start': date2ym(str(request.form['start'])),
            'end': date2ym(str(request.form['end']))
            })
    except Exception as err:
        abort(500, "Parsing assignment failed:\n\n" + str(err))

    try:
        session.commit()
    except Exception as err:
        session.rollback()
        abort(500, "Updating assignment failed:\n\n" + str(err))

    return flask_response(["success"])

@app.route('/del_assignment', methods = ['POST'])
def del_assignment():
    try:
        aid = int(request.form['aid'])
    except Exception as err:
        abort(500, "Incorrect assignment input:\n\n" + str(err))

    engine.execute('DELETE FROM assignments WHERE aid = ' + str(aid))

    return flask_response(["success"])

@app.route('/')
def main_page():
    return redirect('/static/index.html')

# an Engine, which the Session will use for connection
# resources
engine = create_engine('sqlite:///database.db?check_same_thread=False', echo=False)

# create a configured "Session" class
Session = sessionmaker(bind=engine)

# create a Session
session = Session()

Base.metadata.create_all(engine)

if __name__ == "__main__":
    app.run(debug = True)
