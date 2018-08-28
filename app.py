"""
Resources Assignment and VIewing (RAVI) tool
"""

from flask import Flask, Response, json, request, abort, redirect
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from items import Base, Engineer, Project, Assignment
import queries
import sys
import datetime
from builtins import str

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
    data = []
    for e in engine.execute(queries.ENGINEERS):
        d = dict(e)
        d['start'] = ym2date(d['start'])
        d['end'] = ym2date(d['end'])
        data.append(d)
    return flask_response(data)

@app.route('/get_log', methods = ['POST'])
def get_log():
    filterBy = json.loads(request.get_data())

    data = []
    for e in engine.execute(queries.GET_LOG, filterBy):
        d = dict(e)
        d['oldstart'] = ym2date(d['oldstart'])
        d['newstart'] = ym2date(d['newstart'])
        d['oldend'] = ym2date(d['oldend'])
        d['newend'] = ym2date(d['newend'])
        data.append(d)
    return flask_response(data)

@app.route('/get_project_written_hours', methods = ['POST'])
def get_project_written_hours():
    filterBy = json.loads(request.get_data())
    data = []
    for e in engine.execute(queries.PROJECT_WRITTEN_HOURS, filterBy):
        d = dict(e)
        d['date'] = "{:4d}-{:d}".format(d['Year'], d['Month'])
        data.append(d)

    for e in engine.execute(queries.ASSIGNED_FTE_PROJECT, filterBy):
        d = dict(e)
        d['date'] = ym2date(d['date'])
        data.append(d)
    return flask_response(data)

@app.route('/get_engineer_load', methods = ['GET'])
def get_engineer_load():
    data = []
    for e in engine.execute(queries.ENGINEER_LOAD):
        d = dict(e)
        d['start'] = ym2date(d['start'])
        d['end'] = ym2date(d['end'])
        data.append(d)
    return flask_response(data)

@app.route('/get_overview', methods = ['GET'])
def get_overview():
    req = []
    for e in engine.execute(queries.REQUIRED_FTE):
        d = dict(e)
        d['start'] = ym2date(d['start'])
        d['end'] = ym2date(d['end'])
        req.append(d)

    avl = []
    for e in engine.execute(queries.ASSIGNED_FTE_TOTAL):
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
    data = []
    for p in engine.execute(queries.PROJECT_AND_FTES):
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
    filterBy = json.loads(request.get_data())

    data = []
    for a in engine.execute(queries.GET_ASSIGNMENTS, filterBy):
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
