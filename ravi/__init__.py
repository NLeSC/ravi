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

warn_color = {
    'red': '#990000',
    'orange': '#999900',
    'green': '#009900'}

exact_data = None


app = Flask(__name__)


min_date = '0000-01'
max_date = '9999-12'

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


@app.errorhandler(500)
def custom500(error):
    resp = Response(json.dumps({'error': error.description}), 500, mimetype='application/json')
    resp.headers['Access-Control-Allow-Origin'] = '*'
    return resp


@app.route('/get_engineers', methods = ['GET'])
def get_engineers():
    data = []
    for e in db_session.query(Engineer).order_by(Engineer.eid).all():
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
    assignments = db_session.query(Assignment).filter_by(eid=eid).order_by(Assignment.pid).all()
    sort_values = []
    for pid, assignments_grouped in groupby(assignments, lambda a: a.pid):
        ym_fte = [0] * (end - start)
        sort_value = 0
        for a in assignments_grouped:
            sort_value += max(0, (min(a.end, end) - max(a.start, start))) * a.fte
            for i in range(end - start):
                ym_fte[i] += a.fte if a.start <= (i+start) < a.end else 0
        sort_values.append(sort_value)
        data.append({
            'type': 'bar',
            'name': pid,
            'y': ym_fte})
    data = [x for y, x in sorted(zip(sort_values, data), reverse=True)]
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
    current_ym = datetime.date.today().year * 12 + datetime.date.today().month - 1
    data_planned = []
    data_written = []
    assignments = db_session.query(Assignment).filter_by(eid=eid).order_by(Assignment.pid).all()
    x_axis = [ym2fulldate(ym) for ym in range(start, end + 1)]

    sort_values = []
    for pid, assignments_grouped in groupby(assignments, lambda a: a.pid):
        sort_value = 0
        ym_fte_a = [0.0] * (end - start)
        for a in assignments_grouped:
            sort_value += max(0, (min(a.end, end) - max(a.start, start))) * a.fte
            for m in range(end - start):
                ym = m + start
                ym_fte_a[m] += (a.fte if a.start <= ym < a.end else 0)
        sort_values.append(sort_value)
        data_planned.append({
            'type': 'line',
            'name': a.pid,
            'x': x_axis,
            'y': ym_fte_a,
            'showlegend': (exact_data is None), #show this legend only if there are no hours from exact
            'line': {'dash': 'dot'}})
        if exact_data is not None:
            # Written hours
            exact_code = db_session.query(Project.exact_code).filter_by(pid=a.pid).one()[0].split('#')
            written_fte = []
            for ym in range(start, current_ym):
                if len(exact_code) == 1:
                    written_hours = exact_data[(exact_data.exact_code == exact_code[0]) &
                                               (exact_data.exact_id == exact_id) &
                                               (exact_data.ym == ym)].hours.sum()
                else:
                    written_hours = exact_data[(exact_data.exact_code == exact_code[0]) &
                                               (exact_data.hour_code == exact_code[1]) &
                                               (exact_data.exact_id == exact_id) &
                                               (exact_data.ym == ym)].hours.sum()
                written_fte.append(written_hours / 140.0)
            data_written.append({
                'type': 'line',
                'name': a.pid,
                'x': x_axis,
                'y': written_fte,
                'showlegend': True, #show this legend only if there are hours from exact
                'line': {}})
    data_planned = [x for y, x in sorted(zip(sort_values, data_planned), reverse=True)]
    data_written = [x for y, x in sorted(zip(sort_values, data_written), reverse=True)]
    for i, x in enumerate(data_planned):
        x['line']['color'] = (colors * (1+int(i/10)))[i]
    for i, x in enumerate(data_written):
        x['line']['color'] = (colors * (1+int(i/10)))[i]
    data = data_planned + data_written

    # Written hours on non-assigned projects
    if exact_data is not None:
        assigned_projects = [a.pid for a in assignments]
        pc = len(assigned_projects)
        for pid, exact_code in db_session.query(Project.pid, Project.exact_code).\
                filter(~Project.pid.in_(assigned_projects)).all():
            exact_codes = exact_code.split('#')
            if len(exact_codes) == 1:
                exact_hours = exact_data[(exact_data.exact_code == exact_codes[0]) &
                                         (exact_data.exact_id == exact_id)]
            else:
                exact_hours = exact_data[(exact_data.exact_code == exact_codes[0]) &
                                         (exact_data.hour_code == exact_codes[1]) &
                                         (exact_data.exact_id == exact_id)]
            if exact_hours.hours.sum() > 0:
                written_fte = []
                for ym in range(start, current_ym):
                    written_fte.append(float(exact_hours[exact_hours.ym == ym].hours.sum()) / 140.0)
                color = (colors * (1+int(pc/10)))[pc]
                pc += 1
                data.append({
                    'type': 'line',
                    'mode': 'lines',
                    'name': pid,
                    'x': x_axis[:len(written_fte)],
                    'y': written_fte,
                    'showlegend': True, #show this legend only if there are hours from exact
                    'line': {'dash': 'dash', 'color': color}})

    resp = Response(json.dumps(data), mimetype='application/json')
    resp.headers['Access-Control-Allow-Origin'] = '*'
    return resp


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
    resp = Response(json.dumps('[]'), mimetype='application/json')
    resp.headers['Access-Control-Allow-Origin'] = '*'
    return resp


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
    resp = Response(json.dumps(data), mimetype='application/json')
    resp.headers['Access-Control-Allow-Origin'] = '*'
    return resp

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
    resp = Response(json.dumps(data), mimetype='application/json')
    resp.headers['Access-Control-Allow-Origin'] = '*'
    return resp


@app.route('/get_projects', methods = ['GET'])
def get_projects():
    data = []
    for p in db_session.query(Project).order_by(collate(Project.pid, 'NOCASE')).all():
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
    x_axis = [ym2date(ymi) for ymi in range(start, end)]
    plot_data = []
    p = db_session.query(Project).filter_by(pid=pid).one()
    assignments = db_session.query(Assignment).filter_by(pid=pid).order_by(Assignment.eid).all()
    total_planned = 0
    sort_values = []
    for eid, assignments_grouped in groupby(assignments, lambda a: a.eid):
        ym_fte = [0] * (end - start)
        sort_value = 0
        for a in assignments_grouped:
            total_planned += (a.end - a.start) / 12.0 * a.fte
            sort_value += (a.end - a.start) * a.fte
            for i in range(end - start):
                ym_fte[i] += a.fte if a.start <= (i+start) < a.end else 0
        sort_values.append(sort_value)
        name = eid
        if eid[:2] == '00':
            name = '<span style="color:red">' + eid + '</span>'
        plot_data.append({
            'type': 'bar',
            'name': name,
            'y': ym_fte})
    plot_data = [x for y, x in sorted(zip(sort_values, plot_data), reverse=True)]
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
        'planned': '<b>{:.2f}</b><br>{:.2f}'.format(total_planned, p.fte),
        'warn_color': warn_color[color],
        'plot': plot_data
        }
    resp = Response(json.dumps(data), mimetype='application/json')
    resp.headers['Access-Control-Allow-Origin'] = '*'
    return resp

@app.route('/get_project_plot', methods = ['POST'])
def get_project_plot():
    pid = request.form['pid']
    data = get_project_plot_data(pid)
    resp = Response(json.dumps(data), mimetype='application/json')
    resp.headers['Access-Control-Allow-Origin'] = '*'
    return resp

@app.route('/get_all_project_plots_data', methods = ['GET'])
def get_all_project_plots_data():
    data = {pid: get_project_plot_data(pid) for pid, in db_session.query(Project.pid).all()}
    resp = Response(json.dumps(data), mimetype='application/json')
    resp.headers['Access-Control-Allow-Origin'] = '*'
    return resp

def get_project_plot_data(pid):
    current_ym = datetime.date.today().year * 12 + datetime.date.today().month - 1
    data_projected = []
    data_written = []
    p = db_session.query(Project).filter_by(pid=pid).one()
    x_axis = [ym2fulldate(ym) for ym in range(p.start, p.end + 1)]
    exact_code = p.exact_code.split('#')

    # Assigned engineer hours
    assignments = db_session.query(Assignment).filter_by(pid=pid).order_by(Assignment.eid).all()
    projected_total = [0.0] * (p.end - p.start + 1)
    sort_values = []
    for eid, assignments_grouped in groupby(assignments, lambda a: a.eid):
        projected_fte = [0.0] * (p.end - p.start + 1)
        sort_value = 0
        for a in assignments_grouped:
            ym_fte = max(0.0, (min(p.start, a.end) - a.start - 1) * a.fte)
            sort_value += (a.end - a.start) * a.fte
            for m in range(p.end - p.start + 1):
                ym = m + p.start
                # Projected hours
                ym_fte += a.fte if a.start < ym <= a.end else 0
                projected_fte[m] += ym_fte / 12
                projected_total[m] += ym_fte / 12
        sort_values.append(sort_value)
        data_projected.append({
            'type': 'line',
            'mode': 'lines',
            'name': a.eid,
            'x': x_axis,
            'y': projected_fte,
            'showlegend': (exact_data is None or current_ym < p.start), #show this legend only if there are no hours from exact
            'line': {'dash': 'dot'}})
        if exact_data is not None:
            # Written hours
            written_fte = []
            exact_id, = db_session.query(Engineer.exact_id).filter_by(eid=eid).one()
            for ym in range(p.start, current_ym + 1):
                    try:
                        if len(exact_code) == 1:
                            written_hours = exact_data[(exact_data.exact_code == exact_code[0]) &
                                                       (exact_data.exact_id == exact_id) &
                                                       (exact_data.ym < ym)].hours.sum()
                        else:
                            written_hours = exact_data[(exact_data.exact_code == exact_code[0]) &
                                                       (exact_data.hour_code == exact_code[1]) &
                                                       (exact_data.exact_id == exact_id) &
                                                       (exact_data.ym < ym)].hours.sum()
                        written_fte.append(written_hours / 1680.0)
                    except IndexError:
                        written_fte.append(written_fte[-1])
            data_written.append({
                'type': 'line',
                'mode': 'lines',
                'name': a.eid,
                'x': x_axis[:len(written_fte)],
                'y': written_fte,
                'showlegend': True, #show this legend only if there are hours from exact
                'line': {}})
    data_projected = [x for y, x in sorted(zip(sort_values, data_projected), reverse=True)]
    data_written = [x for y, x in sorted(zip(sort_values, data_written), reverse=True)]
    for i, x in enumerate(data_projected):
        x['line']['color'] = (colors * (1+int(i/10)))[i]
    for i, x in enumerate(data_written):
        x['line']['color'] = (colors * (1+int(i/10)))[i]
    data = data_projected + data_written

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
    written_fte = []
    if exact_data is not None:
        for ym in range(p.start, current_ym + 1):
            try:
                if len(exact_code) == 1:
                    written_hours = exact_data[(exact_data.exact_code == exact_code[0]) &
                                               (exact_data.ym < ym)].hours.sum()
                else:
                    written_hours = exact_data[(exact_data.exact_code == exact_code[0]) &
                                               (exact_data.hour_code == exact_code[1]) &
                                               (exact_data.ym < ym)].hours.sum()
                written_fte.append(written_hours / 1680.0)
            except IndexError:
                written_fte.append(written_fte[-1])
        data.append({
            'type': 'line',
            'mode': 'lines',
            'name': 'total written',
            'x': x_axis,
            'y': written_fte,
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
            written_fte = [0]
            for ym in range(p.start, p.end):
                if ym < current_ym:
                    if len(exact_code) == 1:
                        written_hours = exact_data[(exact_data.exact_code == exact_code[0]) &
                                                   (exact_data.exact_id == exact_id) &
                                                   (exact_data.ym == ym)].hours.sum()
                    else:
                        written_hours = exact_data[(exact_data.exact_code == exact_code[0]) &
                                                   (exact_data.hour_code == exact_code[1]) &
                                                   (exact_data.exact_id == exact_id) &
                                                   (exact_data.ym == ym)].hours.sum()
                    written_fte.append(written_fte[-1] + written_hours / 1680.0)
            ec = i + len(assigned_engineers)
            color = (colors * (1+int(ec/10)))[ec]
            data.append({
                'type': 'line',
                'mode': 'lines',
                'name': eid,
                'x': x_axis[:len(written_fte)],
                'y': written_fte,
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
    resp = Response(json.dumps('["success"]'), mimetype='application/json')
    resp.headers['Access-Control-Allow-Origin'] = '*'
    return resp

@app.route('/del_project', methods = ['POST'])
def del_project():
    pid = request.form['pid']
    p = db_session.query(Project).filter_by(pid=unicode(pid)).one()
    db_session.delete(p)
    for a in db_session.query(Assignment).filter_by(pid=pid):
        db_session.delete(a)
    db_session.commit()
    resp = Response(json.dumps('[]'), mimetype='application/json')
    resp.headers['Access-Control-Allow-Origin'] = '*'
    return resp

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
    plt.figure(1)
    projects = db_session.query(Project.pid, Project.coordinator).filter(Project.active == True).all()
    for pid, coordinator in projects:
        folder = output_folder+'/'+coordinator
        try:
            os.makedirs(folder)
        except:
            pass
        data = get_project_plot_data(pid)
        for trace in data:
            style = '-'
            if 'dash' in trace['line']:
                if trace['line']['dash'] == 'dash':
                    style = '--'
                elif trace['line']['dash'] == 'dot':
                    style = ':'
            plt.plot(trace['y'], style, color=trace['line']['color'], label=trace['name'] if trace['showlegend'] else None)
        plt.title('Project: '+pid)
        plt.xticks(range(len(data[0]['x'])), data[0]['x'], rotation=-90)
        plt.tight_layout()
        plt.legend(loc='upper left')
        plt.savefig(folder+'/'+pid+'.pdf')
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
