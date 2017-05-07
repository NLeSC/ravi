"""
Resources Assignment and VIewing (RAVI) tool
"""

from flask import Flask, Response, json, request
from sqlalchemy import create_engine, desc
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import func, desc
from items import Base, Engineer, Project, Assignment, Usersetting
import sys

app = Flask(__name__)


min_date = '0000-01'
max_date = '9999-12'

def ym2date(ym):
    if ym:
        y, m = divmod(ym, 12)
        return "{:4d}-{:d}".format(y, m+1)
    else:
        return None

def date2ym(date):
    if date:
        d = date.split('-')
        return 12*int(d[0]) + int(d[1]) -1
    else:
        return None


@app.route('/get_engineers', methods = ['GET'])
def get_engineers():
    data = []
    for e in db_session.query(Engineer).all():
        d = dict(e)
        d['start'] = ym2date(d['start'])
        d['end'] = ym2date(d['end'])
        data.append(d)
    resp = Response(json.dumps(data), mimetype='application/json')
    resp.headers['Access-Control-Allow-Origin'] = '*'
    return resp

@app.route('/get_engineer_data', methods = ['POST'])
def get_engineer_data():
    eid = request.form['eid']
    start = date2ym(get_start_date())
    end = date2ym(get_end_date())
    data = []
    e = db_session.query(Engineer).filter_by(eid=eid).one()
    assignments = db_session.query(Assignment).filter_by(eid=eid).all()
    assignments.sort(key = lambda a: (min (a.end, end) - max(a.start, start)), reverse=True)
    for a in assignments:
        ym_fte=[a.fte if a.start <= ym < a.end else 0 for ym in range(start, end)]
        data.append({
            'type': 'bar',
            'name': a.pid,
            'y': ym_fte})
    data.append({
        'type': 'line',
        'name': 'fte',
        'x': [x-0.5 for x in range(end-start+1)],
        'y': [e.fte if e.start <= ym <= e.end else 0 for ym in range(start,end+1)],
        'showlegend': len(data) == 0,
        'line': {
            'dash': 'dot',
            'width': 2,
            'color': 'black'}})
    resp = Response(json.dumps(data), mimetype='application/json')
    resp.headers['Access-Control-Allow-Origin'] = '*'
    return resp

@app.route('/add_engineer', methods = ['POST'])
def add_engineer():
    engineer_data = json.loads(request.form['data'])
    try:
        db_session.query(Engineer).filter_by(eid=engineer_data['eid']).update({
            'fte': unicode(engineer_data['fte']),
            'start': date2ym(engineer_data['start']),
            'end': date2ym(engineer_data['end']),
            'exact_id': engineer_data['exact_id']
            })
    except:
        engineer = Engineer()
        engineer.eid = unicode(engineer_data['eid'])
        engineer.exact_id = engineer_data['exact_id']
        engineer.fte = engineer_data['fte']
        engineer.start = date2ym(engineer_data['start'])
        engineer.end = date2ym(engineer_data['end'])
        db_session.add(engineer)
    db_session.commit()
    resp = Response(json.dumps('["success"]'), mimetype='application/json')
    resp.headers['Access-Control-Allow-Origin'] = '*'
    return resp

@app.route('/del_engineer', methods = ['POST'])
def del_engineer():
    eid = request.form['eid']
    e = db_session.query(Engineer).filter_by(eid=eid).one()
    db_session.delete(e)
    for a in db_session.query(Assignment).filter_by(eid=eid):
        db_session.delete(a)
    db_session.commit()
    resp = Response(json.dumps('[]'), mimetype='application/json')
    resp.headers['Access-Control-Allow-Origin'] = '*'
    return resp


@app.route('/get_xaxis_data', methods = ['GET'])
def get_xlabels():
    start = get_start_date()
    end = get_end_date()
    start_ym = date2ym(start)
    end_ym = date2ym(end)
    x_axis = [ym2date(ymi) for ymi in range(start_ym, end_ym)]
    y_axis = [1 for ymi in range(start_ym, end_ym)]
    data = {
        'start_month': start,
        'end_month': end,
        'labels': [{
            'type': 'bar',
            'name': 'months',
            'x': x_axis,
            'y': y_axis}]}
    resp = Response(json.dumps(data), mimetype='application/json')
    resp.headers['Access-Control-Allow-Origin'] = '*'
    return resp

def get_start_date():
    start, = db_session.query(Usersetting.value).filter_by(setting = u'start_date').one()
    return start

def get_end_date():
    end, = db_session.query(Usersetting.value).filter_by(setting = u'end_date').one()
    return end

@app.route('/get_projects', methods = ['GET'])
def get_projects():
    data = []
    for p in db_session.query(Project).all():
        d = dict(p)
        d['start'] = ym2date(d['start'])
        d['end'] = ym2date(d['end'])
        data.append(d)
    resp = Response(json.dumps(data), mimetype='application/json')
    resp.headers['Access-Control-Allow-Origin'] = '*'
    return resp

@app.route('/get_project_data', methods = ['POST'])
def get_project_data():
    pid = request.form['pid']
    start = date2ym(get_start_date())
    end = date2ym(get_end_date())
    data = []
    p = db_session.query(Project).filter_by(pid=pid).one()
    assignments = db_session.query(Assignment).filter_by(pid=pid).all()
    assignments.sort(key = lambda a: (min (a.end, end) - max(a.start, start)), reverse=True)
    for a in assignments:
        ym_fte=[a.fte if a.start <= ym < a.end else 0 for ym in range(start, end)]
        data.append({
            'type': 'bar',
            'name': a.eid,
            'y': ym_fte})
    data.append({
        'type': 'line',
        'name': 'fte',
        'x': [x-0.5 for x in range(end-start+1)],
        'y': [p.fte if p.start <= ym <= p.end else 0 for ym in range(start,end+1)],
        'showlegend': len(data) == 0,
        'line': {
            'dash': 'dot',
            'width': 2,
            'color': 'black'}})
    resp = Response(json.dumps(data), mimetype='application/json')
    resp.headers['Access-Control-Allow-Origin'] = '*'
    return resp

@app.route('/add_project', methods = ['POST'])
def add_project():
    project_data = json.loads(request.form['data'])
    try:
        db_session.query(Project).filter_by(pid=project_data['pid']).update({
            'fte': unicode(project_data['fte']),
            'start': date2ym(project_data['start']),
            'end': date2ym(project_data['end']),
            'exact_code': project_data['exact']
            })
    except:
        project = Project()
        project.pid = unicode(project_data['pid'])
        project.exact_code = project_data['exact']
        project.fte = project_data['fte']
        project.start = date2ym(project_data['start'])
        project.end = date2ym(project_data['end'])
        db_session.add(project)
    db_session.commit()
    resp = Response(json.dumps('["success"]'), mimetype='application/json')
    resp.headers['Access-Control-Allow-Origin'] = '*'
    return resp

@app.route('/del_project', methods = ['POST'])
def del_project():
    pid = request.form['pid']
    p = db_session.query(Project).filter_by(pid=pid).one()
    db_session.delete(p)
    for a in db_session.query(Assignment).filter_by(pid=pid):
        db_session.delete(a)
    db_session.commit()
    resp = Response(json.dumps('[]'), mimetype='application/json')
    resp.headers['Access-Control-Allow-Origin'] = '*'
    return resp

@app.route('/get_assignments', methods = ['POST'])
def get_assignments():
    eid = request.form['eid']
    pid = request.form['pid']
    query = db_session.query(Assignment)
    if eid != "":
        query = query.filter_by(eid=eid)
    if pid != "":
        query = query.filter_by(pid=pid)
    data = []
    for a in query.all():
        d = dict(a)
        d['start'] = ym2date(d['start'])
        d['end'] = ym2date(d['end'])
        data.append(d)
    resp = Response(json.dumps(data), mimetype='application/json')
    resp.headers['Access-Control-Allow-Origin'] = '*'
    return resp
  
@app.route('/add_assignment', methods = ['POST'])
def add_assignment():
    assignment_data = json.loads(request.form['data'])
    sys.stderr.write(str(assignment_data))
    assignment = Assignment()
    assignment.eid = unicode(assignment_data['eid'])
    assignment.pid = unicode(assignment_data['pid'])
    assignment.fte = assignment_data['fte']
    assignment.start = date2ym(assignment_data['start'])
    assignment.end = date2ym(assignment_data['end'])
    db_session.add(assignment)
    db_session.commit()
    resp = Response(json.dumps('["success"]'), mimetype='application/json')
    resp.headers['Access-Control-Allow-Origin'] = '*'
    return resp

@app.route('/del_assignment', methods = ['POST'])
def del_assignment():
    aid = request.form['aid']
    a = db_session.query(Assignment).filter_by(aid=aid).one()
    data = dict(a)
    data['start'] = ym2date(data['start'])
    data['end'] = ym2date(data['end'])
    db_session.delete(a)
    db_session.commit()
    resp = Response(json.dumps(data), mimetype='application/json')
    resp.headers['Access-Control-Allow-Origin'] = '*'
    return resp

@app.route('/get_user_settings', methods = ['GET'])
def get_user_settings():
    data = [dict(s) for s in db_session.query(Usersetting).all()]
    resp = Response(json.dumps(data), mimetype='application/json')
    resp.headers['Access-Control-Allow-Origin'] = '*'
    return resp

@app.route('/set_user_setting', methods = ['POST'])
def set_user_settings():
    setting = request.form['setting']
    value = request.form['value']
    try:
        db_session.query(Usersetting).filter_by(setting=setting).update({'value': value})
    except:
        newsetting = Usersetting()
        newsetting.setting = setting
        newsetting.value = value
        db_session.add(newsetting)
    db_session.commit()
    resp = Response(json.dumps('[]'), mimetype='application/json')
    resp.headers['Access-Control-Allow-Origin'] = '*'
    return resp


def main():
    db_name = sys.argv[1]
    engine = create_engine('sqlite:///' + db_name, echo=False)
    session = sessionmaker()
    session.configure(bind=engine)
    global db_session
    db_session = session()
    Base.metadata.create_all(engine)
    print "Create db"
    if len(db_session.query(Usersetting).all()) < 2:
        start_date = Usersetting(setting = u'start_date', value = u'2015-01')
        end_date = Usersetting(setting = u'end_date', value = u'2019-01')
        db_session.add(start_date)
        db_session.add(end_date)
    db_session.commit()
    app.run(debug = True)

if __name__ == '__main__':
    main(sys.argv)
