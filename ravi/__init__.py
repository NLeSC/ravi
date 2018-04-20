"""
Resources Assignment and VIewing (RAVI) tool
"""

from flask import Flask, Response, json, request, abort
from sqlalchemy import create_engine, desc, collate
from sqlalchemy.orm import sessionmaker, exc
from sqlalchemy.sql import func, desc
from items import Base, Engineer, Project, Assignment, Usersetting
import sys, csv, os
import datetime
from itertools import groupby
import pandas as pd

months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
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
min_date = '0000-01'
max_date = '9999-12'

exact_data = None
current_ym = datetime.date.today().year * 12 + datetime.date.today().month


app = Flask(__name__)


def ym2date(ym):
    if ym:
        y, m = divmod(ym, 12)
        return "{:4d}-{:d}".format(y, m+1)
    else:
        return None

def ym2fulldate(ym):
    if ym:
        y, m = divmod(ym, 12)
        return "{:4d} {:s}".format(y, months[m])
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

def enumerate_assignment_groups(groups, start, end):
    data = []
    sort_values = []
    for name, assignments_grouped in groups:
        ym_fte = [0] * (end - start)
        sort_value = 0
        for a in assignments_grouped:
            for i in range(end - start):
                ym_fte[i] += a.fte if a.start <= (i+start) < a.end else 0
        sort_values.append(sort_value)
        data.append({
            'name': name,
            'y': ym_fte})
    return [x for y, x in sorted(zip(sort_values, data), reverse=True)]

def stack(data):
	for i in range(1, len(data)):
		for j in range(min(len(data[i]['y']), len(data[i-1]['y']))):
			data[i]['y'][j] += data[i-1]['y'][j]

@app.route('/get_engineers', methods = ['GET'])
def get_engineers():
    data = []
    for e in db_session.query(Engineer).order_by(Engineer.eid).all():
        d = dict(e)
        d['start'] = ym2date(d['start'])
        d['end'] = ym2date(d['end'])
        data.append(d)
    return flask_response(data)

@app.route('/get_engineer_data', methods = ['POST'])
def get_engineer_data():
    eid = request.form['eid']
    start = date2ym(get_start_date())
    end = date2ym(get_end_date())
    assignments = db_session.query(Assignment).filter_by(eid=eid).order_by(Assignment.pid).all()
    data = enumerate_assignment_groups(groupby(assignments, lambda a: a.pid), start, end)
    stack(data)
    for i, series in enumerate(data):
        series['fill'] = 'tonexty'
        series['fillcolor'] = colors[i%10]
        series['mode'] = 'none'
    e = db_session.query(Engineer).filter_by(eid=eid).one()
    data.append({
        'type': 'line',
        'name': 'fte',
        'y': [e.fte if e.start <= ym < e.end else 0 for ym in range(start,end+1)],
        'showlegend': len(data) == 0,
        'line': {
            'dash': 'dot',
            'width': 2,
            'color': 'black'}})
    return flask_response(data)

def list_written_fte(written_hours, start, end):
    written_fte = []
    for ym in range(start, end):
        try:
            written_fte.append(written_hours[exact_data.ym == ym].hours.sum() / 140.0)
        except IndexError:
            written_fte.append(written_fte[-1])
    return written_fte

@app.route('/get_engineer_plot', methods = ['POST'])
def get_engineer_plot():
    """
    Returns data needed for a detailed plot of planned and written hours for an engineer
    """
    eid = request.form['eid']
    exact_id = request.form['exact']
    start = date2ym(get_start_date())
    end = date2ym(get_end_date())
    assignments = db_session.query(Assignment).filter_by(eid=eid).order_by(Assignment.pid).all()
    x_axis = [ym2fulldate(ym) for ym in range(start, end + 1)]
    data_written = []
    data_planned = enumerate_assignment_groups(groupby(assignments, lambda a: a.pid), start, end)
    for series in data_planned:
        series['type'] = 'line'
        series['x'] = x_axis
        series['showlegend'] = (exact_data is None) #show this legend only if there are no hours from exact
        series['line'] = {'dash': 'dot'}

        pid = series['name']
        if exact_data is not None:
            # Written hours
            exact_code = db_session.query(Project.exact_code).filter_by(pid=pid).one()[0].split('#')
            select_hours = exact_data[(exact_data.exact_code == exact_code[0]) &
                                      (exact_data.exact_id == exact_id)]
            if len(exact_code) > 1:
                select_hours = select_hours[exact_data.hour_code == exact_code[1]]
            data_written.append({
                'type': 'line',
                'name': pid,
                'x': x_axis,
                'y': list_written_fte(select_hours, start, current_ym),
                'showlegend': True, #show this legend only if there are hours from exact
                'line': {}})
    for i, x in enumerate(data_planned):
        x['line']['color'] = colors[i%10]
    for i, x in enumerate(data_written):
        x['line']['color'] = colors[i%10]
    data = data_planned + data_written

    # Written hours on non-assigned projects
    if exact_data is not None:
        assigned_projects = [a.pid for a in assignments]
        pc = len(assigned_projects)
        for pid, exact_code in db_session.query(Project.pid, Project.exact_code).\
                filter(~Project.pid.in_(assigned_projects)).all():
            exact_codes = exact_code.split('#')
            select_hours = exact_data[(exact_data.exact_code == exact_codes[0]) &
                                      (exact_data.exact_id == exact_id)]
            if len(exact_codes) > 1:
                select_hours = select_hours[(exact_data.hour_code == exact_codes[1])]
            if select_hours.hours.sum() > 0:
                written_fte = []
                color = colors[pc%10]
                pc += 1
                data.append({
                    'type': 'line',
                    'mode': 'lines',
                    'name': pid,
                    'x': x_axis,
                    'y': list_written_fte(select_hours, start, current_ym),
                    'showlegend': True, #show this legend only if there are hours from exact
                    'line': {'dash': 'dash', 'color': color}})

    return flask_response(data)


@app.route('/add_engineer', methods = ['POST'])
def add_engineer():
    try:
        engineer_data = json.loads(request.form['data'])
        if 0 == db_session.query(Engineer).filter_by(eid=engineer_data['eid']).update({
                'fte': unicode(engineer_data['fte']),
                'start': date2ym(engineer_data['start']),
                'end': date2ym(engineer_data['end']),
                'exact_id': engineer_data['exact_id'],
                'comments': engineer_data['comments'],
                'active': engineer_data['active']
                }):
            engineer = Engineer()
            engineer.eid = unicode(engineer_data['eid'])
            engineer.exact_id = engineer_data['exact_id']
            engineer.fte = engineer_data['fte']
            engineer.start = date2ym(engineer_data['start'])
            engineer.end = date2ym(engineer_data['end'])
            engineer.comments = engineer_data['comments']
            engineer.active = engineer_data['active']
            db_session.add(engineer)
    except Exception as err:
        abort(500, "Incorrect engineer input:\n\n" + str(err))
    try:
        db_session.commit()
    except Exception as err:
        db_session.rollback()
        abort(500, "Adding engineer failed:\n\n" + str(err))
    return flask_response(["success"])

@app.route('/del_engineer', methods = ['POST'])
def del_engineer():
    eid = request.form['eid']
    e = db_session.query(Engineer).filter_by(eid=eid).one()
    db_session.delete(e)
    for a in db_session.query(Assignment).filter_by(eid=eid):
        db_session.delete(a)
    db_session.commit()
    return flask_response([])

@app.route('/rename_engineer', methods = ['POST'])
def rename_engineer():
    eid = request.form['eid']
    newid = request.form['newid']
    e = db_session.query(Engineer).filter_by(eid=unicode(eid)).one()
    db_session.delete(e)
    e.eid = newid
    db_session.add(e)
    db_session.query(Assignment).filter_by(eid=eid).update({'eid': newid})
    db_session.commit()
    return flask_response([])

@app.route('/get_xaxis_data', methods = ['GET'])
def get_xlabels():
    start = get_start_date()
    end = get_end_date()
    start_ym = date2ym(start)
    end_ym = date2ym(end)
    x_axis = [ym2fulldate(ymi) for ymi in range(start_ym, end_ym)]
    y_axis = [1 for ymi in range(start_ym, end_ym)]
    data = {
        'start_month': start,
        'end_month': end,
        'labels': [{
            'type': 'bar',
            'name': 'months',
            'x': x_axis,
            'y': y_axis}]}
    return flask_response(data)

def get_start_date():
    start, = db_session.query(Usersetting.value).filter_by(setting = u'start_date').one()
    return start

def get_end_date():
    end, = db_session.query(Usersetting.value).filter_by(setting = u'end_date').one()
    return end

@app.route('/get_total_assignments_plot', methods = ['GET'])
def get_total_assignments_plot():
    start = date2ym(get_start_date())
    end = date2ym(get_end_date())
    x_axis = [ym2date(ym) for ym in range(start, end)]
    assignments = db_session.query(Assignment).all()
    engineers = db_session.query(Engineer).all()
    engineer_list = [e.eid for e in engineers if e.eid[:2] != '00']
    dummy_list = [e.eid for e in engineers if e.eid[:2] == '00']
    engineer_ids = [e.exact_id for e in engineers if e.eid[:2] != '00']
    projects = db_session.query(Project).all()
    project_codes = [p.exact_code.split('#')[0] for p in projects if p.fte > 0]
    total_fte = []
    total_written = []
    total_assigned = []
    dummy_assigned = []
    for ym in range(start,end):
        total_assigned.append(sum([a.fte for a in assignments if a.start <= ym < a.end and a.eid in engineer_list]))
        dummy_assigned.append(sum([a.fte for a in assignments if a.start <= ym < a.end and a.eid in dummy_list]))
        total_fte.append(sum([e.fte for e in engineers if e.start <= ym < e.end]))
        total_written.append(float(exact_data[(exact_data.ym == ym) &
                                              (exact_data.exact_id.isin(engineer_ids)) &
                                              (exact_data.exact_code.isin(project_codes))].hours.sum()) / 140.0)
        # To check for missing projects on which hours were writtten after july 2017
        # print exact_data[(~exact_data.exact_code.isin(project_codes)) & (exact_data.ym > 24210)].exact_code.unique()
    data = [
        {
            'type': 'bar',
            'name': 'real assignments',
            'x': x_axis,
            'y': total_assigned
            },
        {
            'type': 'bar',
            'name': 'dummy assignments',
            'x': x_axis,
            'y': dummy_assigned
            },
        {
            'type': 'line',
            'name': 'total engineers',
            'x': x_axis,
            'y': total_fte,
            'line': {
                'dash': 'dot',
                'width': 2,
                'color': 'black'}
            },
        {
            'type': 'line',
            'name': 'total written on projects',
            'x': x_axis,
            'y': total_written,
            'line': {
                #'dash': 'dot',
                'width': 2,
                'color': 'blue'}
            }]
    return flask_response(data)


@app.route('/get_projects', methods = ['GET'])
def get_projects():
    data = []
    for p in db_session.query(Project).order_by(collate(Project.pid, 'NOCASE')).all():
        d = dict(p)
        d['start'] = ym2date(d['start'])
        d['end'] = ym2date(d['end'])
        data.append(d)
    return flask_response(data)

@app.route('/get_project_data', methods = ['POST'])
def get_project_data():
    pid = request.form['pid']
    start = date2ym(get_start_date())
    end = date2ym(get_end_date())
    x_axis = [ym2date(ymi) for ymi in range(start, end)]
    assignments = db_session.query(Assignment).filter_by(pid=pid).order_by(Assignment.eid).all()
    plot_data = enumerate_assignment_groups(groupby(assignments, lambda a: a.eid), start, end)
    stack(plot_data)
    for i, series in enumerate(plot_data):
        series['fill'] = 'tonexty'
        series['fillcolor'] = colors[i%10]
        series['mode'] = 'none'
        if series['name'][:3] == '00_':
            series['name'] = '<span style="color:red">' + series['name'] + '</span>'

    total_planned = sum([a.fte * (a.end - a.start) / 12 for a in assignments])
    p = db_session.query(Project).filter_by(pid=pid).one()
    if p.fte == 0:
        color = 'red'
    else:
        ratio = total_planned / p.fte
        if 0.95 < ratio < 1.01:
            color = 'green'
        elif 0.8 < ratio < 1.05:
            color = 'orange'
        else:
            color = 'red'
    data = {
        'planned': '<font color="{}">{:.2f} / {:.2f}</font>'.format(color, total_planned, p.fte),
        'plot': plot_data
        }
    return flask_response(data)

@app.route('/get_project_plot', methods = ['POST'])
def get_project_plot():
    pid = request.form['pid']
    data = get_project_plot_data(pid)
    return flask_response(data)

@app.route('/get_all_project_plots_data', methods = ['GET'])
def get_all_project_plots_data():
    data = {pid: get_project_plot_data(pid) for pid, in db_session.query(Project.pid).all()}
    return flask_response(data)

def accumulate_written_fte(written_hours, start, end):
    written_fte = []
    for ym in range(start, end):
        try:
            written_fte.append(written_hours[exact_data.ym < ym].hours.sum() / 1680.0)
        except IndexError:
            written_fte.append(written_fte[-1])
    return written_fte

def get_project_plot_data(pid):
    """
    Returns data needed for a detailed plot of planned and written hours for a project
    """
    data_written = []
    p = db_session.query(Project).filter_by(pid=pid).one()
    assignments = db_session.query(Assignment).filter_by(pid=pid).order_by(Assignment.eid).all()
    # Make sure the x-axis covers all assignments
    start = min([p.start] + [a.start for a in assignments])
    end = max([p.end] + [a.end for a in assignments])
    if exact_data is not None:
        exact_code = p.exact_code.split('#')
        # Select all hours written on the project
        project_hours = exact_data[(exact_data.exact_code == exact_code[0])]
        if len(exact_code) > 1:
            project_hours = project_hours[project_hours.hour_code == exact_code[1]]
        # Make sure the x-axis covers all written hours on the project
        start = min([start] + list(project_hours['ym']))
        end = max([end] + list(project_hours['ym']))
    end += 1
    x_axis = [ym2fulldate(ym) for ym in range(start, end)]

    # Assigned engineer hours
    projected_total = [0.0] * (end - start)

    data_projected = enumerate_assignment_groups(groupby(assignments, lambda a: a.eid), start, end)
    for series in data_projected:
        if exact_data is not None:
            eid = series['name']
            # Written hours
            exact_id = db_session.query(Engineer.exact_id).filter_by(eid=eid).first()
            if exact_id == None:
                continue

            written_fte = accumulate_written_fte(project_hours[(exact_data.exact_id == exact_id[0])], start, current_ym)
            data_written.append({
                'type': 'line',
                'mode': 'lines',
                'name': eid,
                'x': x_axis,
                'y': written_fte,
                'showlegend': bool(sum(written_fte) > 0), #show this legend only if there are hours from exact
                'line': {}})
        # accumulate the data
        series['y'] = [sum(series['y'][:i])/12 for i in range(end - start)]
        projected_total = [projected_total[i] + series['y'][i] for i in range(end - start)]
        series['type'] = 'line'
        series['mode'] = 'lines'
        series['x'] = x_axis
        series['showlegend'] = (exact_data is None or bool(sum(written_fte) == 0)) #show this legend only if there are no hours from exact
        series['line'] = {'dash': 'dot'}

    for i, x in enumerate(data_projected):
        x['line']['color'] = colors[i%10]
    for i, x in enumerate(data_written):
        x['line']['color'] = colors[i%10]
    data = data_written + data_projected

    # total projected hours
    data.append({
        'type': 'line',
        'mode': 'lines',
        'name': 'total',
        'x': x_axis,
        'y': projected_total,
        'showlegend': (exact_data is None),
        'line': {'dash': 'dot', 'color': 'black'}})

    # Total written hours
    if exact_data is not None:
        select_hours = exact_data[exact_data.exact_code == exact_code[0]]
        if len(exact_code) > 1:
            select_hours = select_hours[exact_data.hour_code == exact_code[1]]
        data.append({
            'type': 'line',
            'mode': 'lines',
            'name': 'total written',
            'x': x_axis,
            'y': accumulate_written_fte(select_hours, start, current_ym),
            'showlegend': True,
            'line': {'color': 'black'}})

    # Written hours by non-assigned engineers
    if exact_data is not None:
        assigned_engineers = [eid for eid, a in groupby(assignments, lambda a: a.eid)]
        if len(exact_code) == 1:
            writing_engineers = exact_data[exact_data.exact_code == exact_code[0]].groupby('exact_id').count().index.values
        else:
            writing_engineers = exact_data[(exact_data.exact_code == exact_code[0]) & (exact_data.hour_code == exact_code[1])].\
                groupby('exact_id').count().index.values
        writing_engineer_ids = db_session.query(Engineer).filter(Engineer.exact_id.in_(writing_engineers)).all()
        other_engineers = [(e.eid, e.exact_id) for e in writing_engineer_ids if e.eid not in assigned_engineers]
        for i, (eid, exact_id) in enumerate(other_engineers):
            select_hours = exact_data[(exact_data.exact_code == exact_code[0]) &
                                      (exact_data.exact_id == exact_id)]
            if len(exact_code) > 1:
                select_hours = select_hours[exact_data.hour_code == exact_code[1]]
            ec = i + len(assigned_engineers)
            color = colors[ec%10]

            data.append({
                'type': 'line',
                'mode': 'lines',
                'name': eid,
                'x': x_axis,
                'y': accumulate_written_fte(select_hours, start, current_ym),
                'showlegend': True, #show this legend only if there are hours from exact
                'line': {'dash': 'dash', 'color': color}})

    return data

@app.route('/add_project', methods = ['POST'])
def add_project():
    try:
        project_data = json.loads(request.form['data'])
        if 0 == db_session.query(Project).filter_by(pid=project_data['pid']).update({
                'fte': float(project_data['fte']),
                'start': date2ym(project_data['start']),
                'end': date2ym(project_data['end']),
                'exact_code': unicode(project_data['exact_code']),
                'coordinator': unicode(project_data['coordinator']),
                'comments': unicode(project_data['comments']),
                'active': project_data['active']
                }):
            project = Project()
            project.pid = unicode(project_data['pid'])
            project.exact_code = unicode(project_data['exact_code'])
            project.fte = float(project_data['fte'])
            project.start = date2ym(project_data['start'])
            project.end = date2ym(project_data['end'])
            project.coordinator = unicode(project_data['coordinator'])
            project.comments = unicode(project_data['comments'])
            project.active = project_data['active']
            db_session.add(project)
    except Exception as err:
        abort(500, "Incorrect project input:\n\n" + str(err))
    try:
        db_session.commit()
    except Exception as err:
        db_session.rollback()
        abort(500, "Adding project failed:\n\n" + str(err))
    return flask_response(["success"])

@app.route('/del_project', methods = ['POST'])
def del_project():
    pid = request.form['pid']
    p = db_session.query(Project).filter_by(pid=unicode(pid)).one()
    db_session.delete(p)
    for a in db_session.query(Assignment).filter_by(pid=pid):
        db_session.delete(a)
    db_session.commit()
    return flask_response([])

@app.route('/rename_project', methods = ['POST'])
def rename_project():
    pid = request.form['pid']
    newid = request.form['newid']
    p = db_session.query(Project).filter_by(pid=unicode(pid)).one()
    db_session.delete(p)
    p.pid = newid
    db_session.add(p)
    db_session.query(Assignment).filter_by(pid=pid).update({'pid': newid})
    db_session.commit()
    return flask_response([])

@app.route('/get_assignments', methods = ['POST'])
def get_assignments():
    eid = request.form['eid']
    pid = request.form['pid']
    query = db_session.query(Assignment)
    if eid != "":
        query = query.filter_by(eid=eid)
    if pid != "":
        query = query.filter_by(pid=pid)
    query = query.order_by(Assignment.pid, Assignment.eid, Assignment.start)
    data = []
    for a in query.all():
        d = dict(a)
        d['start'] = ym2date(d['start'])
        d['end'] = ym2date(d['end'])
        data.append(d)
    return flask_response(data)
  
@app.route('/add_assignment', methods = ['POST'])
def add_assignment():
    try:
        assignment_data = json.loads(request.form['data'])
        assignment = Assignment()
        assignment.eid = unicode(assignment_data['eid'])
        assignment.pid = unicode(assignment_data['pid'])
        assignment.fte = assignment_data['fte']
        assignment.start = date2ym(assignment_data['start'])
        assignment.end = date2ym(assignment_data['end'])
        db_session.add(assignment)
    except Exception as err:
        abort(500, "Incorrect assignment input:\n\n" + str(err))
    try:
        db_session.commit()
    except Exception as err:
        db_session.rollback()
        abort(500, "Adding assignment failed:\n\n" + str(err))
    return flask_response(["success"])

@app.route('/del_assignment', methods = ['POST'])
def del_assignment():
    aid = request.form['aid']
    a = db_session.query(Assignment).filter_by(aid=aid).one()
    data = dict(a)
    data['start'] = ym2date(data['start'])
    data['end'] = ym2date(data['end'])
    db_session.delete(a)
    db_session.commit()
    return flask_response(data)

@app.route('/get_user_settings', methods = ['GET'])
def get_user_settings():
    data = [dict(s) for s in db_session.query(Usersetting).all()]
    return flask_response(data)

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
    return flask_response([])

def read_exact_data(filename):
    global exact_data
    hours = {}
    hours_total = {}
    with open(filename, "r") as csvfile:
        reader = csv.DictReader(csvfile)
        for ln, line in enumerate(reader):
            try:
                day, month, year = line['Datum'].split('-')
                ym = date2ym("-".join([year,month]))
                t = (unicode(line['Projectcode']), unicode(line['Uur- of kostensoort (Code)']), unicode(line['Medewerker ID']), ym)
                if t in hours:
                    hours[t] += int(float(line['Aantal']))
                else:
                    hours[t] = int(float(line['Aantal']))
            except:
                sys.stderr.write("Exact file could not be read at line " + str(ln+1) + "\n")
    data = [list(k) + [v] for k,v in hours.items()]
    exact_data = pd.DataFrame(data, columns=['exact_code', 'hour_code', 'exact_id', 'ym', 'hours'])
    return exact_data

def create_all_project_plots(output_folder):
    import matplotlib.pyplot as plt
    import matplotlib.patheffects as path_effects
    try:
        os.makedirs(output_folder)
    except OSError as error:
        sys.stderr.write(str(error))
    projects = db_session.query(Project).filter(Project.active == True).all()
    for p in projects:
        assignments = db_session.query(Assignment).filter_by(pid = p.pid).order_by(Assignment.eid, Assignment.start).all()
        total_planned = sum([a.fte * (a.end - a.start) / 12 for a in assignments])
        text = 'Person-years budgetted: {:.2f}\nPerson-years planned:   {:.2f}\n'.format(p.fte, total_planned)
        text += 'Time-stamp:             {}\n\n'.format(datetime.datetime.now())
        text += 'Planning\n------------------------------------------------'
        for a in assignments:
            text += '\n{:15s} {:.1f} fte      {:s} - {:s}'.format(a.eid, a.fte, ym2fulldate(a.start), ym2fulldate(a.end))
        plt.figure(1, figsize=(10,15))
        folder = output_folder+'/'+p.coordinator
        try:
            os.makedirs(folder)
        except:
            pass
        data = get_project_plot_data(p.pid)
        for trace in data:
            style = '-'
            if 'dash' in trace['line']:
                if trace['line']['dash'] == 'dash':
                    style = '--'
                elif trace['line']['dash'] == 'dot':
                    style = ':'
            plt.plot(trace['y'], style, color=trace['line']['color'], label=trace['name'] if trace['showlegend'] else None)
        plt.title('Project: '+p.pid)
        plt.xticks(range(len(data[0]['x'])), data[0]['x'], rotation=-90)
        plt.subplots_adjust(bottom=0.6)
        plt.legend(loc='upper left')
        plt.figtext(0.1, 0.5, text, verticalalignment='top', family='monospace')
        plt.savefig(folder+'/'+p.pid+'.pdf')
        plt.close()


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
    if len(db_session.query(Usersetting).all()) < 2:
        start_date = Usersetting(setting = u'start_date', value = u'2015-01')
        end_date = Usersetting(setting = u'end_date', value = u'2019-01')
        db_session.add(start_date)
        db_session.add(end_date)
    db_session.commit()
    if len(sys.argv) == 4:
        create_all_project_plots(sys.argv[3])
        exit()
    app.run(debug = True)

if __name__ == '__main__':
    main(sys.argv)
