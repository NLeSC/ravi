"""
Resources Assignment and VIewing (RAVI) tool
"""

from flask import Flask, Response, json, request, abort
from sqlalchemy import create_engine, desc
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import func, desc
from items import Base, Engineer, Project, Assignment, Usersetting
import sys, csv, os
import datetime
from itertools import groupby
import pandas as pd

colors = ['#1f77b4',
    '#ff7f0e',
    '#2ca02c',
    '#d62728',
    '#9467bd',
    '#8c564b',
    '#e377c2',
    '#7f7f7f',
    '#bcbd22',
    '#17becf',
    "#1f77b4",
    "#ff7f0e"]

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
    assignments = db_session.query(Assignment).filter_by(eid=eid).all()
    assignments.sort(key = lambda a: (min (a.end, end) - max(a.start, start)), reverse=True)
    for pid, assignments_grouped in groupby(assignments, lambda a: a.pid):
        ym_fte = [0] * (end - start)
        for a in assignments_grouped:
            for i in range(end - start):
                ym_fte[i] += a.fte if a.start <= (i+start) < a.end else 0
        data.append({
            'type': 'bar',
            'name': pid,
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
    current_ym = datetime.date.today().year * 12 + datetime.date.today().month - 1
    data = []
    assignments = db_session.query(Assignment).filter_by(eid=eid).all()
    assignments.sort(key = lambda a: (min (a.end, end) - max(a.start, start)), reverse=True)
    ym_fte_t = [0 for ym in range(start, end)]
    x = [ym2date(ym) for ym in range(start, end)]
    for i, a in enumerate(assignments):
        ym_fte_a = [a.fte if a.start <= ym < a.end else 0 for ym in range(start, end)]
        ym_fte_t = [ym_fte_t[ym-start] + (a.fte if a.start <= ym < a.end else 0) for ym in range(start, end)]
        data.insert(0, {
            'type': 'line',
            'name': a.pid,
            'x': x,
            'y': ym_fte_a,
            'showlegend': (exact_data is None), #show this legend only if there are no hours from exact
            'line': {'dash': 'dot', 'color': colors[i]}})
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
            data.insert(0, {
                'type': 'line',
                'name': a.pid,
                'x': x,
                'y': written_fte,
                'showlegend': True, #show this legend only if there are hours from exact
                'line': {'color': colors[i]}})
#    data.append({
#        'type': 'line',
#        'name': 'total',
#        'x': x,
#        'y': ym_fte_t,
#        'line': {'dash': 'dot', 'color': 'black'}})
    # Written hours on non-assigned projects
    if exact_data is not None:
        assigned_projects = [a.pid for a in assignments]
        project_count = len(assigned_projects)
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
                project_count += 1
                written_fte = []
                for ym in range(start, current_ym):
                    written_fte.append(float(exact_hours[exact_hours.ym == ym].hours.sum()) / 140.0)
                if project_count > 10:
                    color = 'black'
                else:
                    color = colors[project_count]
                data.append({
                    'type': 'line',
                    'mode': 'lines',
                    'name': pid,
                    'x': x[:len(written_fte)],
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
                'comments': engineer_data['comments']
                }):
            engineer = Engineer()
            engineer.eid = unicode(engineer_data['eid'])
            engineer.exact_id = engineer_data['exact_id']
            engineer.fte = engineer_data['fte']
            engineer.start = date2ym(engineer_data['start'])
            engineer.end = date2ym(engineer_data['end'])
            engineer.comments = engineer_data['comments']
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
    for p in db_session.query(Project).order_by(Project.pid).all():
        d = dict(p)
        d['start'] = ym2date(d['start'])
        d['end'] = ym2date(d['end'])
        data.append(d)
    sys.stderr.write(str(data))
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
    #assignments.sort(key = lambda a: (min (a.end, end) - max(a.start, start)), reverse=True)
    # ToDo: this sorting messes up the grouping by engineer, are there other ways to sort to
    # make the "gantcharts" nicer
    total_planned = 0
    for eid, assignments_grouped in groupby(assignments, lambda a: a.eid):
        ym_fte = [0] * (end - start)
        for a in assignments_grouped:
            total_planned += (a.end - a.start) / 12.0 * a.fte
            for i in range(end - start):
                ym_fte[i] += a.fte if a.start <= (i+start) < a.end else 0
        plot_data.append({
            'type': 'bar',
            'name': eid,
            # 'x': x_axis,
            'y': ym_fte})
    """
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
    """
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
    sys.stderr.write(str(data))
    resp = Response(json.dumps(data), mimetype='application/json')
    resp.headers['Access-Control-Allow-Origin'] = '*'
    return resp

def get_project_plot_data(pid):
    current_ym = datetime.date.today().year * 12 + datetime.date.today().month - 1
    data = []
    p = db_session.query(Project).filter_by(pid=pid).one()
    x = [ym2date(ym) for ym in range(p.start, p.end + 1)]
    exact_code = p.exact_code.split('#')

    # Assigned engineer hours
    assignments = db_session.query(Assignment).filter_by(pid=pid).order_by(Assignment.eid).all()
    #assignments.sort(key = lambda a: (min (a.end, p.end) - max(a.start, p.start)), reverse=True)
    projected_total = [0.0] * (p.end - p.start + 1)
    for i, (eid, assignments_grouped) in enumerate(groupby(assignments, lambda a: a.eid)):
        # make sure lines don't overlap for engineer with equal assignments
        projected_fte = [0] * (p.end - p.start + 1)
        for a in assignments_grouped:
            ym_fte = 0
            for m in range(p.end - p.start):
                ym = m + p.start
                # Projected hours
                ym_fte += a.fte if a.start <= ym < a.end else 0
                projected_fte[m+1] += ym_fte / 12
                projected_total[m+1] += ym_fte / 12
        data.insert(0, {
            'type': 'line',
            'mode': 'lines',
            'name': a.eid,
            'x': x,
            'y': projected_fte,
            'showlegend': (exact_data is None), #show this legend only if there are no hours from exact
            'line': {'dash': 'dot', 'color': colors[i]}})
        if exact_data is not None:
            # Written hours
            written_fte = [0]
            exact_id, = db_session.query(Engineer.exact_id).filter_by(eid=eid).one()
            for ym in range(p.start, current_ym):
                if ym < current_ym:
                    try:
                        if len(exact_code) == 1:
                            written_hours = exact_data[(exact_data.exact_code == exact_code[0]) &
                                                       (exact_data.exact_id == exact_id) &
                                                       (exact_data.ym == ym)].hours.values[0]
                        else:
                            written_hours = exact_data[(exact_data.exact_code == exact_code[0]) &
                                                       (exact_data.hour_code == exact_code[1]) &
                                                       (exact_data.exact_id == exact_id) &
                                                       (exact_data.ym == ym)].hours.values[0]
                        written_fte.append(written_fte[-1] + written_hours / 1680.0)
                    except IndexError:
                        written_fte.append(written_fte[-1])
            data.insert(0, {
                'type': 'line',
                'mode': 'lines',
                'name': a.eid,
                'x': x[:len(written_fte)],
                'y': written_fte,
                'showlegend': True, #show this legend only if there are hours from exact
                'line': {'color': colors[i]}})

    # total projected hours
    data.append({
        'type': 'line',
        'mode': 'lines',
        'name': 'total',
        'x': x,
        'y': projected_total,
        'showlegend': (exact_data is None),
        'line': {'dash': 'dot', 'color': 'black'}})

    # Total written hours
    written_fte = [0]
    if exact_data is not None:
        for ym in range(p.start, current_ym):
            try:
                written_hours = exact_data[(exact_data.exact_code == p.exact_code) & 
                                           (exact_data.ym == ym)].hours.sum()
                written_fte.append(written_fte[-1] + written_hours / 1680.0)
            except IndexError:
                written_fte.append(written_fte[-1])
        data.append({
            'type': 'line',
            'mode': 'lines',
            'name': 'total written',
            'x': x,
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
            colornr = i + len(assigned_engineers)
            if colornr > 10:
                color = 'black'
            else:
                color = colors[colornr]
            data.append({
                'type': 'line',
                'mode': 'lines',
                'name': eid,
                'x': x[:len(written_fte)],
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
                'comments': unicode(project_data['comments'])
                }):
            sys.stderr.write(str(project_data))
            project = Project()
            project.pid = unicode(project_data['pid'])
            project.exact_code = unicode(project_data['exact_code'])
            project.fte = float(project_data['fte'])
            project.start = date2ym(project_data['start'])
            project.end = date2ym(project_data['end'])
            project.coordinator = unicode(project_data['coordinator'])
            project.comments = unicode(project_data['comments'])
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
    projects = db_session.query(Project.pid, Project.coordinator).all()
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
