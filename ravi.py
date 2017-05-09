"""
Resources Assignment and VIewing (RAVI) tool
"""

from flask import Flask, Response, json, request
from sqlalchemy import create_engine, desc
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import func, desc
from items import Base, Engineer, Project, Assignment, Usersetting
import sys, csv
import datetime

colors = ['#1f77b4',
    '#ff7f0e',
    '#2ca02c',
    '#d62728',
    '#9467bd',
    '#8c564b',
    '#e377c2',
    '#7f7f7f',
    '#bcbd22',
    '#17becf']

hours = None
hours_total = None


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

@app.route('/get_engineer_plot', methods = ['POST'])
def get_engineer_plot():
    eid = request.form['eid']
    exact_id = request.form['exact']
    start = date2ym(get_start_date())
    end = date2ym(get_end_date())
    data = []
    assignments = db_session.query(Assignment).filter_by(eid=eid).all()
    assignments.sort(key = lambda a: (min (a.end, end) - max(a.start, start)), reverse=True)
    ym_fte_t = [0 for ym in range(start, end)]
    x = [ym2date(ym) for ym in range(start, end)]
    for i, a in enumerate(assignments):
        ym_fte_a = [a.fte if a.start <= ym < a.end else 0 for ym in range(start, end)]
        ym_fte_t = [ym_fte_t[ym-start] + (a.fte if a.start <= ym < a.end else 0) for ym in range(start, end)]
        data.append({
            'type': 'line',
            'name': a.pid,
            'x': x,
            'y': ym_fte_a,
            'showlegend': (hours is None), #show this legend only if there are no hours from exact
            'line': {'dash': 'dot', 'color': colors[i]}})
        if hours:
            exact_code, = db_session.query(Project.exact_code).filter_by(pid=a.pid).one()
            ym_fte_w = [hours[(str(exact_code), str(exact_id), ym)]/140.0 if (str(exact_code), str(exact_id), ym) in hours else 0 for ym in range(start, end)]
            data.append({
                'type': 'line',
                'name': a.pid,
                'x': x,
                'y': ym_fte_w,
                'showlegend': (hours is not None), #show this legend only if there are hours from exact
                'line': {'color': colors[i]}})
    data.append({
        'type': 'line',
        'name': 'total',
        'x': x,
        'y': ym_fte_t,
        'line': {'dash': 'dot', 'color': 'black'}})
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

@app.route('/get_project_plot', methods = ['POST'])
def get_project_plot():
    pid = request.form['pid']
    start = date2ym(get_start_date())
    end = date2ym(get_end_date())
    data = []
    p = db_session.query(Project).filter_by(pid=pid).one()
    x = [ym2date(ym) for ym in range(p.start, p.end)]

    # total projected hours
    projected_total_fte = [(i+1) * p.fte/12 for i in range(p.end - p.start)]
    data = [({
        'type': 'line',
        'name': 'total',
        'x': x,
        'y': projected_total_fte,
        'showlegend': (hours_total is None),
        'line': {'dash': 'dot', 'color': 'black'}})]

    # Total written hours
    written_fte = [0]
    current_ym = datetime.date.today().year * 12 + datetime.date.today().month - 1
    if hours_total:
        for ym in range(p.start, current_ym):
            index = (str(p.exact_code), ym)
            written_hours = hours_total[index] if (index in hours_total) else 0
            written_fte.append(written_fte[-1] + written_hours / 1680.0)
        data.append({
            'type': 'line',
            'name': 'total written',
            'x': x,
            'y': written_fte,
            'showlegend': (hours_total is not None),
            'line': {'color': 'black'}})

    # Assigned engineer hours
    assignments = db_session.query(Assignment).filter_by(pid=pid).all()
    assignments.sort(key = lambda a: (min (a.end, end) - max(a.start, start)), reverse=True)
    for i, a in enumerate(assignments):
        # make sure lines don't overlap for engineer with equal assignments
        if len(assignments) > 1:
            projected_fte = [(i-len(assignments)/2.0+0.5)/30.0]
        else:
            projected_fte = [0]
        written_fte = [0]
        for ym in range(p.start, p.end):
            # Projected hours
            ym_fte = a.fte if a.start <= ym < a.end else 0
            projected_fte.append(projected_fte[-1] + ym_fte / 12)
            if hours:
                # Written hours
                exact_id, = db_session.query(Engineer.exact_id).filter_by(eid=a.eid).one()
                if ym < current_ym:
                    index = (str(p.exact_code), str(exact_id), ym)
                    written_hours = hours[index] if (index in hours) else 0
                    written_fte.append(written_fte[-1] + written_hours / 1680.0)
        data.append({
            'type': 'line',
            'name': a.eid,
            'x': x,
            'y': projected_fte,
            'showlegend': (hours is None), #show this legend only if there are no hours from exact
            'line': {'dash': 'dot', 'color': colors[i]}})
        if hours:
            data.append({
                'type': 'line',
                'name': a.eid,
                'x': x[:len(written_fte)],
                'y': written_fte,
                'showlegend': (hours is not None), #show this legend only if there are hours from exact
                'line': {'color': colors[i]}})
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

def read_exact_data(filename):
    global hours, hours_total
    hours = {}
    hours_total = {}
    with open(filename, "r") as csvfile:
        reader = csv.DictReader(csvfile)
        for ln, line in enumerate(reader):
            try:
                day, month, year = line['Datum'].split('-')
                ym = date2ym("-".join([year,month]))
                t = (line['Projectcode'], line['Medewerker ID'], ym)
                if t in hours:
                    hours[t] += int(float(line['Aantal']))
                else:
                    hours[t] = int(float(line['Aantal']))
                t = (line['Projectcode'], ym)
                if t in hours_total:
                    hours_total[t] += int(float(line['Aantal']))
                else:
                    hours_total[t] = int(float(line['Aantal']))
            except:
                sys.stderr.write("Exact file could not be read at line " + str(ln+1) + "\n")

def main():
    db_name = sys.argv[1]
    if len(sys.argv) > 2:
        read_exact_data(sys.argv[2])
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
