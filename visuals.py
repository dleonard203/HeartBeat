from sql_schemas import *
import plotly.plotly as py
import plotly.graph_objs as go
import plotly
import json
import datetime

YELLOW = "#e0db41"
GREEN = "#1f610b"
RED = "#9c3321"


def blood_globals():
    with open('globals.json', 'r') as fin:
        return json.load(fin)

def no_data(chart_name):
    return f"<div class=\"no_data\"><h3>No data for: {chart_name}<h3></div>"

def weight_chart(sql_records):
    data = []
    x, y, annotations = get_x_y_text(sql_records, 'timestamp', 'weight')
    if len(x) == 0:
        return no_data("daliy weight line chart")
    data.append(go.Scatter(x=x, y=y, name="weight over time"))
    #layout = go.Layout(title="Weight (last 30 days)", plot_bgcolor='rgba(107, 209, 82, 0.116)', paper_bgcolor='rgba(107, 209, 82, 0.116)')
    layout = go.Layout(title="Weight (last 30 days)")
    fig = go.Figure(data=data, layout=layout)

    return plotly.offline.plot(fig, include_plotlyjs=False, output_type="div")



def blood_pies(sql_records):
    levels = blood_globals()
    pre_safe = pre_high = pre_low = post_high = post_low = post_safe = 0
    colors = [RED, GREEN, YELLOW]
    for record in sql_records:
        val = record.blood_sugar
        #pre-meal
        if record.meal_status == 0:
            if val < levels['min_pre']:
                pre_low += 1
            elif val > levels['max_pre']:
                pre_high += 1
            else:
                pre_safe +=1
        #post_meal
        else:
            if val < levels['min_post']:
                post_low += 1
            elif val > levels['max_post']:
                post_high += 1
            else:
                post_safe += 1
    if pre_low + pre_high + pre_safe > 0:
        labels_low = [f"High (> {levels['max_pre']})", 'Normal', f"Low (< {levels['min_pre']})"]
        trace_pre = go.Pie(labels=labels_low, values=[pre_high, pre_safe, pre_low], marker=dict(colors=colors), sort=False)
        layout = go.Layout(title="Blood Sugar (pre-meal)")
        fig = go.Figure(data=[trace_pre], layout=layout)
        div_pre = plotly.offline.plot(fig, include_plotlyjs=False, output_type="div")
    else:
        div_pre = no_data("pre-meal blood sugars pie chart")

    if post_low + post_high + post_safe > 0:
        labels_post = [f"High (> {levels['max_post']})", 'Normal', f"Low (< {levels['min_post']})"]
        trace_post = go.Pie(labels = labels_post, values=[post_high, post_safe, post_low], marker=dict(colors=colors), sort=False)
        layout = go.Layout(title="Blood Sugar (post-meal)")
        fig = go.Figure(data=[trace_post], layout=layout)
        div_post = plotly.offline.plot(fig, include_plotlyjs=False, output_type="div")
    else:
        div_post = no_data("post-meal blood sugars pie chart")

    return [div_pre, div_post]
            
    

# good for non-complicated charts
def get_x_y_text(sql_recs, x_attr, y_attr, text_attr=None, cond=lambda rec: True):
    x, y, annotations = [], [], []
    args_dict = {}
    for rec in sql_recs:
        if cond(rec):
            x.append(rec.__getattribute__(x_attr))
            y.append(rec.__getattribute__(y_attr))
            if text_attr != None:
                annotations.append(rec.__getattribute__(text_attr).replace('\n', '<br>'))
    return x, y, annotations


def determine_bar_colors(values, tpe):
    results = []
    levels = blood_globals()
    for value in values:
        if tpe == 'pre':
            if value < levels['min_pre']:
                results.append(YELLOW)
            elif value > levels['max_pre']:
                results.append(RED)
            else:
                results.append(GREEN)
        else:
            if value < levels['min_post']:
                results.append(YELLOW)
            elif value > levels['max_post']:
                results.append(RED)
            else:
                results.append(GREEN)
    return results


def generate_individual_bar(x, y, annotations, tpe, mn, mx):
    dt_format = '%Y-%m-%d %H:%M:%S'
    if len(x) == 0:
        div = no_data(f"{tpe}-meal blood sugar bar chart")
    else:
        trace = go.Bar(x=x, y=y, text=annotations, marker=dict(color=determine_bar_colors(y, tpe)))
        layout = go.Layout(title=f"{tpe}-meal blood sugar".capitalize())
        x00_pt = str(datetime.datetime.strptime(x[0], dt_format) + datetime.timedelta(days=1))
        x01_pt = str(datetime.datetime.strptime(x[len(x) - 1], dt_format) - datetime.timedelta(days=1))
        if len(x) > 1:
            layout.update(dict(shapes = [
                {'type': 'rect',
                'xref': 'x',
                'yref': 'y',
                'x0': x00_pt,
                'y0': mn,
                'x1': x01_pt,
                'y1': mn,
                'fillcolor': RED,
                'line': {'color': RED},
                'opacity': 0.9},
                {'type': 'rect',
                'xref': 'x',
                'yref': 'y',
                'x0': x00_pt,
                'y0': mx,
                'x1': x01_pt,
                'y1': mx,
                'fillcolor': RED,
                'line': {'color': RED},
                'opacity': 0.9}
            ]),
            annotations=[go.Annotation(text=f"Lowest normal<br>{tpe}-meal blood sugar<br>({mn})", x=x00_pt, y=mn,
            font=dict(color="#000000"), bgcolor='#ff7f0e'),
            go.Annotation(text=f"Highest normal<br>{tpe}-meal blood sugar<br>({mx})", x=x01_pt, y=mx,
            font=dict(color="#000000"), bgcolor='#ff7f0e')]
            )
        fig = go.Figure(data=[trace], layout=layout)
        div = plotly.offline.plot(fig, include_plotlyjs=False, output_type="div")
    return div



def blood_bars(sql_recs):
    x_pre, y_pre, annotations_pre = get_x_y_text(sql_recs, 'timestamp', 'blood_sugar', text_attr='symptoms', cond=lambda rec: rec.__getattribute__('meal_status') == 0)
    x_post, y_post, annotations_post = get_x_y_text(sql_recs, 'timestamp', 'blood_sugar', text_attr='symptoms', cond=lambda rec: rec.__getattribute__('meal_status') == 1)
    levels = blood_globals()
    div_pre = generate_individual_bar(x_pre, y_pre, annotations_pre, 'pre', levels['min_pre'], levels['max_pre'])
    div_post = generate_individual_bar(x_post, y_post, annotations_post, 'post', levels['min_post'], levels['max_post'])

    return [div_pre, div_post]
