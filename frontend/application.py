# -*- coding: utf-8 -*-
import dash
import dash_core_components as dcc
import dash_html_components as html
import pandas as pd
import numpy as np
import plotly.graph_objs as go
import os
from random import randrange
from datetime import datetime



external_stylesheets = ['assetes/external_sytlesheet.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

app.scripts.config.serve_locally=True



def read_cases_data():
    '''
    load the data
    '''
    df_cases = pd.read_excel(r'\data-cases\cases.xlsx')
    return df_cases

def create_15_days(start_date):
    date_list = pd.date_range(start=start_date, end=start_date+15)
    date_list = [str(date)[:10] for date in date_list]
    return date_list

def create_timeline():
    df = read_cases_data()
    start = '2/1/2020' #TODO replace with first date in our data
    end = datetime.today().strftime('%Y-%m-%d')
    date_list = pd.date_range(start=start, end =end)
    return date_list

def read_action_data():
    df = pd.read_csv(r'data-actions/policymeasures - measures_taken.csv')
    # Drop any row, which does not contain the bare minimum required for generating an action-marker.
    df = df.dropna(subset=["startdate_action", "enddate_action", "geographic_level", "location", "action"], how="any")

    # convert columns to datetime which contain datetime.
    df["startdate_action"] = pd.to_datetime(df["startdate_action"])
    df["enddate_action"] = pd.to_datetime(df["enddate_action"])
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    return df

def build_bar_chart_data():
    df = read_cases_data()
    # x = create_timeline() # the time line we want to show
    bar_charts =[]
    color = ['#B3B3B3','#171717']

    for i,land in enumerate(['NRW','Bayern']):
        x= df['Time']
        y=df[land]
        # y = [randrange(10) for i in range(len(x))] # replace with actual cases
        data = go.Bar(
            x=x,
            y=y,
            name = land,
            marker_color = color[i]
        )
        bar_charts.append(data)
    return bar_charts

am_hover_template = """
<b>%{{text}}</b><br>
{details_action}
<extra></extra>
"""

def build_am_data():
    df = read_cases_data()
    max_cases = max(df['NRW'])/len(df)

    action_data = read_action_data()
    action_data = action_data.sort_values("startdate_action")
    for row_num, action in action_data.iterrows():
        print([action["action"],] * 2)
        break
    data = [go.Scatter(
                    x=[action["startdate_action"], action["startdate_action"]+np.timedelta64(15, 'D')],
                    y=[-1*row_num,-1*row_num],
                    marker={"size": 16,
                            "symbol": "triangle-down",
                            "color":"green"},
                    mode="lines+markers+text",
                    name=action["action"],
                    hovertemplate=am_hover_template.format(details_action=action["details_action"]), #TODO: Evaluate what is possible with this template and what is impossible.
                    text=[action["action"], "mögl. Effekt"],
                    textposition="bottom center",
                    )
                for row_num, action in action_data.iterrows()
            ]
    return data

def create_action_marker_chart():
    am_data = build_am_data()
    am_layout = go.Layout(xaxis=dict(title="time", type="category"),
                          yaxis=dict(title="measures", type="category"),
                          showlegend=False)
    am_fig = go.Figure(data=am_data, layout=am_layout)
    am_chart = dcc.Graph(id='actions', figure=am_fig)
    return am_chart

def create_bar_chart():
    bar_data = build_bar_chart_data()
    bar_layout = go.Layout(
        xaxis=dict(
            # tickmode='linear',
    showgrid = False,
               ticks = '',
                       showticklabels = False
                   ) # range is the initial zoom on 16 days with the possibility to zoom out
        ,yaxis=dict(title="Number of cases"))

    bar_fig = go.Figure(data=bar_data, layout=bar_layout)
    bar_fig.update_xaxes(tickangle=90)
    bar_chart = dcc.Graph(id= 'bar_chart', figure=bar_fig)
    return bar_chart

def merge_figures():
    '''
    Merge the plots with add trace
    '''
    fig = go.Figure()
    am_figure = build_am_data()
    bar_figure = build_bar_chart_data()
    for am in am_figure:
        fig.add_trace(am)
    for bar in bar_figure:
        fig.add_trace(bar)

    for trace in fig['data']:
        if (trace['name'] == 'trace10'): trace['showlegend'] = False

    fig.update_xaxes(tickangle=90)
    fig.update_layout(
        barmode='group',
        plot_bgcolor ='white',
        xaxis=dict(
            tickmode='linear',
                   # range=[count_days-focus,count_days]
        ), # range is the initial zoom on 16 days with the possibility to zoom out
        yaxis=dict(title="Number of cases"))
    graph = dcc.Graph(id= 'Timeline', figure=fig)
    return graph


def normalize_data():
    '''
    normalize the data with population
    :return:
    '''

dropdown_bundesland = dcc.Dropdown(
        id='bundesland',
        options=[
            {'label': 'NRW', 'value': 'NRW'},
            {'label': 'Bayern', 'value': 'Bayern'},
        ],
        value='NRW',
    multi=True
    )

dropdown_landkreis = dcc.Dropdown(
        id='landkreis',
        options=[
            {'label': 'Köln', 'value': 'Köln'},
            {'label': 'Aachen', 'value': 'Aachen'},
        ],
        value='Köln',
    multi=True
    )

bar_chart = create_bar_chart()
am_chart = create_action_marker_chart()
plot = merge_figures()

app.layout = html.Div(children=[
    html.H1(children='''
    Timeline of Events in Germany
    '''),
    # bar_chart,
    # am_chart
   dropdown_bundesland,
    dropdown_landkreis,
    plot

])

if __name__ == '__main__':
    print('reload')
    app.run_server(host="0.0.0.0", debug=True)
