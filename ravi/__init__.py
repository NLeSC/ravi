"""
Resources Assignment and VIewing (RAVI) tool
"""

from flask import Flask, Response, json, request, abort
from sqlalchemy import create_engine, desc, collate
from sqlalchemy.orm import sessionmaker, exc
from sqlalchemy.sql import func, desc
from .items import Base, Engineer, Project, Assignment, Usersetting
import sys, csv, os
import datetime
from itertools import groupby
import pandas as pd
from builtins import str

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
current_ym = datetime.date.today().year * 12 + datetime.date.today().month - 1


app = Flask(__name__)


def date2dat(date):
    if date:
        return "{:4d}-{:d}".format(date.year, date.month)
    else:
        return None

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

def dat2ym(dat):
#    print "DAT:", dat
    if dat:
        d = dat.split('-')
        return 12 * int(d[0]) + int(d[1]) - 1
    else:
        return None

def date2ym(date):
#    print "DATE:", date
    if date:
        return 12 * date.year + date.month - 1
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
    for gid, assignments_grouped in groups:
        ym_fte = [0] * (end - start)
        sort_value = 0
        for a in assignments_grouped:
            sort_value += max(0, (min(date2ym(a.assignment_end), end) - max(date2ym(a.assignment_start), start))) * a.fte
            for i in range(end - start):
                ym_fte[i] += a.fte if date2ym(a.assignment_start) <= (i+start) < date2ym(a.assignment_end) else 0
        sort_values.append(sort_value)
        data.append({
            'id': gid,
            'y': ym_fte})
    return [x for y, x in sorted(zip(sort_values, data), key=lambda tup:tup[0], reverse=True)]

def stack(data):
	for i in range(1, len(data)):
		for j in range(min(len(data[i]['y']), len(data[i-1]['y']))):
			data[i]['y'][j] += data[i-1]['y'][j]

@app.route('/get_engineers', methods = ['GET'])
def get_engineers():
    data = []
    for e in db_session.query(Engineer).filter(Engineer.tag.in_(('engineer', 'MT', 'Techlead'))).order_by(Engineer.sname).all():
        d = dict(e)
        d['contract_start'] = date2dat(d['contract_start'])
        d['contract_end'] = date2dat(d['contract_end'])
        data.append(d)
    return flask_response(data)

@app.route('/get_engineer_data', methods = ['POST'])
def get_engineer_data():
    eid = request.form['eid']
    start = dat2ym(get_start_date())
    end = dat2ym(get_end_date())
    projectname = dict(db_session.query(Project.project_id, Project.sname).all())
    assignments = db_session.query(Assignment).filter_by(person_id=eid).order_by(Assignment.project_id).all()
    data = enumerate_assignment_groups(groupby(assignments, lambda a: a.project_id), start, end)
    stack(data)
    for i, series in enumerate(data):
        series['name'] = projectname[series['id']]
        series['fill'] = 'tonexty'
        series['fillcolor'] = colors[i%10]
        series['mode'] = 'none'
    e = db_session.query(Engineer).filter_by(person_id=eid).one()
    if e.contract_start == None:
        e.contract_start = 0
    if e.contract_end == None:
        e.contract_end = 120000
    data.append({
        'type': 'line',
        'name': 'fte',
        'y': [e.fte if date2ym(e.contract_start) <= ym < date2ym(e.contract_end) else 0 for ym in range(start,end+1)],
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
    start = dat2ym(get_start_date())
    end = dat2ym(get_end_date())
    assignments = db_session.query(Assignment).filter_by(person_id=eid).order_by(Assignment.project_id).all()
    projectname = dict(db_session.query(Project.project_id, Project.sname).all())
    x_axis = [ym2fulldate(ym) for ym in range(start, end + 1)]
    data_written = []
    data_planned = enumerate_assignment_groups(groupby(assignments, lambda a: a.project_id), start, end)
    for series in data_planned:
        series['type'] = 'line'
        series['x'] = x_axis
        series['showlegend'] = (exact_data is None) #show this legend only if there are no hours from exact
        series['line'] = {'dash': 'dot'}

        pid = series['id']
        series['name'] = projectname[pid]
        if exact_data is not None:
            # Written hours
            exact_code = db_session.query(Project.exact_id).filter_by(project_id=pid).one()[0].split('#')
            select_hours = exact_data[(exact_data.exact_code == exact_code[0]) &
                                      (exact_data.exact_id == exact_id)]
            if len(exact_code) > 1:
                select_hours = select_hours[exact_data.hour_code == exact_code[1]]
            data_written.append({
                'type': 'line',
                'name': projectname[pid],
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
        assigned_projects = [a.project_id for a in assignments]
        pc = len(assigned_projects)
        for pid, exact_code in db_session.query(Project.project_id, Project.exact_id).\
                filter(~Project.project_id.in_(assigned_projects)).all():
            if exact_code is None:
                exact_code = ""
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
                    'name': projectname[pid],
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
                'fte': str(engineer_data['fte']),
                'start': date2ym(engineer_data['start']),
                'end': date2ym(engineer_data['end']),
                'exact_id': engineer_data['exact_id'],
                'comments': engineer_data['comments'],
                'active': engineer_data['active']
                }):
            engineer = Engineer()
            engineer.eid = str(engineer_data['eid'])
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
    person_id = request.form['eid']
    e = db_session.query(Engineer).filter_by(person_id=eid).one()
    db_session.delete(e)
    for a in db_session.query(Assignment).filter_by(person_id=eid):
        db_session.delete(a)
    db_session.commit()
    return flask_response([])

@app.route('/rename_engineer', methods = ['POST'])
def rename_engineer():
    eid = request.form['eid']
    newid = request.form['newid']
    e = db_session.query(Engineer).filter_by(eid=str(eid)).one()
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
    start_ym = dat2ym(start)
    end_ym = dat2ym(end)
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
#    start, = db_session.query(Usersetting.value).filter_by(setting = u'start_date').one()
    start = '2018-01'
    return start

def get_end_date():
#    end, = db_session.query(Usersetting.value).filter_by(setting = u'end_date').one()
    end = '2021-01'
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
    total_projects = []
    for ym in range(start,end):
        total_assigned.append(sum([a.fte for a in assignments if a.start <= ym < a.end and a.eid in engineer_list]))
        total_projects.append(sum([p.fte / (p.end - p.start) * 12 for p in projects if p.start <= ym < p.end]))
        dummy_assigned.append(sum([a.fte for a in assignments if a.start <= ym < a.end and a.eid in dummy_list and ym > current_ym]))
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
            'name': 'total projects',
            'x': x_axis,
            'y': total_projects,
            'line': {
                'dash': 'dash',
                'width': 2,
                'color': 'red'}
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
    for p in db_session.query(Project).order_by(collate(Project.sname, 'NOCASE')).all():
        d = dict(p)
        d['project_start'] = date2dat(d['project_start'])
        d['project_end'] = date2dat(d['project_end'])
        if d['budget'] > 0:
            d['fte'] = d['budget'] / 1680  
        data.append(d)
    return flask_response(data)

def get_totals(project):
    assignments = db_session.query(Assignment).filter_by(project_id=project.project_id)
    total_planned = sum([a.fte * (date2ym(a.assignment_end) - date2ym(a.assignment_start)) / 12 for a in assignments])
    total_combined = total_planned
    if exact_data is not None and project.project_start is not None:
        project_hours = get_project_hours(project.exact_id)
        total_written_fte = accumulate_written_fte(project_hours, date2ym(project.project_start), current_ym + 1)
        if len(total_written_fte) > 0:
            rest_planned = sum([a.fte * (max(date2ym(a.assignment_end), current_ym) - max(date2ym(a.assignment_start), current_ym)) / 12 for a in assignments])
            total_combined = total_written_fte[-1] + rest_planned
    return total_planned, total_combined

def get_color(planned, allocated):
    if allocated is None or allocated == 0:
        return 'red'
    else:
        ratio = planned / allocated
        if 0.95 < ratio < 1.01:
            return 'green'
        if 0.8 < ratio < 1.05:
            return 'orange'
        return 'red'

@app.route('/get_project_data', methods = ['POST'])
def get_project_data():
    pid = request.form['pid']
    start = dat2ym(get_start_date())
    end = dat2ym(get_end_date())
    x_axis = [ym2date(ymi) for ymi in range(start, end)]
    personname = dict(db_session.query(Engineer.person_id, Engineer.sname).all())
    assignments = db_session.query(Assignment).filter_by(project_id=pid).order_by(Assignment.person_id).all()
    grouped_data = groupby(assignments, lambda a: a.person_id)
    plot_data = enumerate_assignment_groups(grouped_data, start, end)
    stack(plot_data)
    for i, series in enumerate(plot_data):
        series['name'] = personname[series['id']]
        series['fill'] = 'tonexty'
        series['fillcolor'] = colors[i%10]
        series['mode'] = 'none'
        #if series['name'][:3] == '00_':
        #    series['name'] = '<span style="color:red">' + series['name'] + '</span>'

    p = db_session.query(Project).filter_by(project_id=pid).one()
    if p.budget > 0:
        p.fte = p.budget / 1680
    else:
        p.fte = 0
    total_planned, total_combined = get_totals(p)
    color_planned = get_color(total_planned, p.fte)
    color_combined = get_color(total_combined, p.fte)
    data = {
        'planned': '''<span title='{1:.2f} Out of {2:.2f} person years are assigned in total to project "{3}".'>
                      <font color="{0}">{1:.2f} / {2:.2f}</font></span>'''.format(color_planned, total_planned, p.fte, p.sname),
        'combined': '''<span title='{1:.2f} Out of {2:.2f} person years are written so far, plus still assigned, to project "{3}".'>
                      <font color="{0}">{1:.2f} / {2:.2f}</font></span>'''.format(color_combined, total_combined, p.fte, p.sname),
        'plot': plot_data
        }
    return flask_response(data)

@app.route('/get_project_plot', methods = ['POST'])
def get_project_plot():
    pid = request.form['pid']
    history = request.form['history']
    data = get_project_plot_data(pid, history=="true")
    return flask_response(data)

@app.route('/get_all_project_plots_data', methods = ['GET'])
def get_all_project_plots_data():
    data = {pid: get_project_plot_data(pid) for pid, in db_session.query(Project.pid).all()}
    return flask_response(data)

def get_project_hours(exact_code):
    ec = exact_code.split('#')
    # Select all hours written on the project
    project_hours = exact_data[(exact_data.exact_code == ec[0])]
    if len(ec) > 1:
        project_hours = project_hours[project_hours.hour_code == ec[1]]
    return project_hours

def accumulate_written_fte(written_hours, start, end):
    written_fte = []
    for ym in range(start, end):
        try:
            written_fte.append(written_hours[exact_data.ym < ym].hours.sum() / 1680.0)
        except IndexError:
            written_fte.append(written_fte[-1])
    return written_fte

def get_project_plot_data(pid, history=False):
    """
    Returns data needed for a detailed plot of planned and written hours for a project
    """
    data_written = []
    p = db_session.query(Project).filter_by(project_id=pid).one()
    assignments = db_session.query(Assignment).filter_by(project_id=pid).order_by(Assignment.person_id).all()
    personname = dict(db_session.query(Engineer.person_id, Engineer.sname).all())
    # Make sure the x-axis covers all assignments
    start = min([date2ym(p.project_start)] + [date2ym(a.assignment_start) for a in assignments])
    end = max([date2ym(p.project_end)] + [date2ym(a.assignment_end) for a in assignments])
    if exact_data is not None:
        project_hours = get_project_hours(p.exact_id)
        # Make sure the x-axis covers all written hours on the project
        start = min([start] + list(project_hours['ym']))
        end = max([end] + list(project_hours['ym']))
        exact_ids = [i[0] for i in db_session.query(Engineer.exact_id).all()]
        project_engineer_hours = project_hours[exact_data.exact_id.isin(exact_ids)]
        total_written_fte = accumulate_written_fte(project_engineer_hours, start, min(current_ym, end) + 1)
    end += 1
    x_axis = [ym2fulldate(ym) for ym in range(start, end)]
    combine_written_planned = exact_data is not None and not history and len(total_written_fte) > 0
    # Determine the offset for the projected hours
    projected_total = [total_written_fte[-1]] * (end - current_ym) if combine_written_planned else [0.0] * (end - start)

    data = [{
        'x': x_axis,
        'y': [p.budget/1680] * (end - start),
        'fill': 'tozeroy',
        'fillcolor': '#eeeeee',
        'mode': 'none',
        'showlegend': False,
        'line': {}
        }]
    data_projected = enumerate_assignment_groups(groupby(assignments, lambda a: a.person_id), start, end)
    for series in data_projected:
        person_id = series['id']
        series['name'] = personname[person_id]
        if exact_data is not None:
            # Written hours
            exact_id = db_session.query(Engineer.exact_id).filter_by(person_id=person_id).first()
            if exact_id == None:
                continue

            written_fte = accumulate_written_fte(project_hours[(exact_data.exact_id == exact_id[0])], start, min(current_ym+1, end))
            data_written.append({
                'type': 'line',
                'mode': 'lines',
                'name': personname[person_id],
                'x': x_axis,
                'y': written_fte,
                'showlegend': bool(sum(written_fte) > 0), #show this legend only if there are hours from exact
                'line': {}})
        # accumulate the data
        if combine_written_planned:
            offset = current_ym-start
            projected_total = [projected_total[i] + sum(series['y'][offset:i+offset])/12 for i in range(end - current_ym)]
            series['y'] = [written_fte[-1] + sum(series['y'][offset:i+offset])/12 for i in range(end - current_ym)]
            series['x'] = x_axis[offset:]
        else:
            series['y'] = [sum(series['y'][:i])/12 for i in range(end - start)]
            projected_total = [projected_total[i] + series['y'][i] for i in range(end - start)]
            series['x'] = x_axis
        series['type'] = 'line'
        series['mode'] = 'lines'
        series['showlegend'] = (exact_data is None or bool(sum(written_fte) == 0)) #show this legend only if there are no hours from exact
        series['line'] = {'dash': 'dot'}

    for i, x in enumerate(data_projected):
        x['line']['color'] = colors[i%10]
    for i, x in enumerate(data_written):
        x['line']['color'] = colors[i%10]
    data += data_written + data_projected

    # total projected hours
    xax = x_axis[current_ym-start:] if combine_written_planned else x_axis
    data.append({
        'type': 'line',
        'mode': 'lines',
        'name': 'total',
        'x': xax,
        'y': projected_total,
        'showlegend': (exact_data is None),
        'line': {'dash': 'dot', 'color': 'black'}})

    # Total written hours
    if exact_data is not None:
        data.append({
            'type': 'line',
            'mode': 'lines',
            'name': 'total written',
            'x': x_axis,
            'y': total_written_fte,
            'showlegend': True,
            'line': {'color': 'black'}})

    # Written hours by non-assigned engineers
    if exact_data is not None:
        assigned_engineers = [person_id for person_id, a in groupby(assignments, lambda a: a.person_id)]
        writing_engineers = project_hours.groupby('exact_id').count().index.values
        writing_engineer_ids = db_session.query(Engineer).filter(Engineer.exact_id.in_(writing_engineers)).all()
        other_engineers = [(e.person_id, e.exact_id) for e in writing_engineer_ids if e.person_id not in assigned_engineers]
        for i, (person_id, exact_id) in enumerate(other_engineers):
            select_hours = project_hours[(exact_data.exact_id == exact_id)]
            ec = i + len(assigned_engineers)
            color = colors[ec%10]

            data.append({
                'type': 'line',
                'mode': 'lines',
                'name': personname[person_id],
                'x': x_axis,
                'y': accumulate_written_fte(select_hours, start, min(current_ym+1, end)),
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
                'exact_code': str(project_data['exact_code']),
                'coordinator': str(project_data['coordinator']),
                'comments': str(project_data['comments']),
                'active': project_data['active']
                }):
            project = Project()
            project.pid = str(project_data['pid'])
            project.exact_code = str(project_data['exact_code'])
            project.fte = float(project_data['fte'])
            project.start = date2ym(project_data['start'])
            project.end = date2ym(project_data['end'])
            project.coordinator = str(project_data['coordinator'])
            project.comments = str(project_data['comments'])
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
    p = db_session.query(Project).filter_by(pid=str(pid)).one()
    db_session.delete(p)
    for a in db_session.query(Assignment).filter_by(pid=pid):
        db_session.delete(a)
    db_session.commit()
    return flask_response([])

@app.route('/rename_project', methods = ['POST'])
def rename_project():
    pid = request.form['pid']
    newid = request.form['newid']
    p = db_session.query(Project).filter_by(pid=str(pid)).one()
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
        person_id, = db_session.query(Engineer.person_id).filter_by(sname=eid).one()
        query = query.filter_by(person_id=person_id)
    if pid != "":
        project_id, = db_session.query(Project.project_id).filter_by(sname=pid).one()
        query = query.filter_by(project_id=project_id)
    query = query.order_by(Assignment.project_id, Assignment.person_id, Assignment.assignment_start)
    data = []
    personname = dict(db_session.query(Engineer.person_id, Engineer.sname).all())
    projectname = dict(db_session.query(Project.project_id, Project.sname).all())
    for a in query.all():
        d = dict(a)
        d['start'] = date2dat(d['assignment_start'])
        d['end'] = date2dat(d['assignment_end'])
        d['eid'] = personname[d['person_id']]
        d['pid'] = projectname[d['project_id']]
        data.append(d)
    return flask_response(data)
  
@app.route('/add_assignment', methods = ['POST'])
def add_assignment():
    try:
        assignment_data = json.loads(request.form['data'])
        assignment = Assignment()
        assignment.eid = str(assignment_data['eid'])
        assignment.pid = str(assignment_data['pid'])
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
        reader = csv.DictReader(csvfile, delimiter='\t')
        for ln, line in enumerate(reader):
            try:
                day, month, year = line['Datum'].split('-')
                ym = dat2ym("-".join([year,month]))
                t = (str(line['Projectcode']), str(line['Uur- of kostensoort (Code)']), str(line['Medewerker ID']), ym)
                if t in hours:
                    hours[t] += int(float(line['Aantal']))
                else:
                    hours[t] = int(float(line['Aantal']))
            except Exception as error:
                sys.stderr.write("Exact file could not be read at line " + str(ln+1) + "\n" + str(error) + "\n")
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
    projects = db_session.query(Project).filter(Project.status == "active").all()
    for p in projects:
        total_planned, total_combined = get_totals(p)
        text = 'Person-years budgetted: {:.2f}\nWritten + planned:      {:.2f}\n'.format(p.fte, total_combined)
        text += 'Start date:             {}\nEnd date:               {}\n'.format(ym2fulldate(p.start), ym2fulldate(p.end))
        text += 'Time-stamp:             {}\n\n'.format(datetime.datetime.now())
        text += 'Planning\n------------------------------------------------'
        assignments = db_session.query(Assignment).filter_by(pid = p.pid).order_by(Assignment.eid, Assignment.start).all()
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
            if 'fill' in trace:
                plt.fill_between(range(len(trace['y'])),0,trace['y'], facecolor=trace['fillcolor'])
            else:
                xaxis = range(len(trace['y']))
                style = '-'
                if 'dash' in trace['line']:
                    if trace['line']['dash'] == 'dash':
                        style = '--'
                    elif trace['line']['dash'] == 'dot':
                        style = ':'
                        xaxis = range(len(data[0]['y'])-len(trace['y']), len(data[0]['y']))
                plt.plot(xaxis, trace['y'], style, color=trace['line']['color'], label=trace['name'] if trace['showlegend'] else None)
        for spine in plt.gca().spines.values():
            spine.set_visible(False)
        plt.title('Project: '+p.pid)
        plt.ylabel('Person-years')
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
    engine = create_engine('sqlite:///' + db_name + '?check_same_thread=False', echo=False)
    session = sessionmaker()
    session.configure(bind=engine)
    global db_session
    db_session = session()
    #Base.metadata.create_all(engine)
#    if len(db_session.query(Usersetting).all()) < 2:
#        start_date = Usersetting(setting = u'start_date', value = u'2015-01')
#        end_date = Usersetting(setting = u'end_date', value = u'2019-01')
#        db_session.add(start_date)
#        db_session.add(end_date)
#    db_session.commit()
    if len(sys.argv) == 4:
        create_all_project_plots(sys.argv[3])
        exit()
    app.run(debug = True)

if __name__ == '__main__':
    main(sys.argv)
