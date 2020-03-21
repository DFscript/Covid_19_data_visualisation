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

def clean_data(df):
    '''
    Clean the data e.g. drop na
    '''
    df =  df[df['timestamp'].notna()] #drop na in column timestamp for action csv
    return df

# def read_data():
#     '''
#     load the data
#     '''
#     # df_cases = pd.read_csv(path_cases,sep = ',')
#     df_actions = clean_data(pd.read_csv(os.path.join("../data-actions", "policymeasures - measures_taken.csv")))
#     return df_actions

def create_15_days(start_date):
    date_list = pd.date_range(start=start_date, end=start_date+15)
    date_list = [str(date)[:10] for date in date_list]
    return date_list

def create_timeline():
    start = '2/1/2020' #TODO replace with first date in our data
    end = datetime.today().strftime('%Y-%m-%d')
    date_list = pd.date_range(start=start, end =end)
    # date_list =[str(date)[:10] for date in date_list]
    return date_list

def read_action_data():

    df = pd.read_csv(r"data-actions/policymeasures - measures_taken.csv")
    # Drop any row, which does not contain the bare minimum required for generating an action-marker.
    df = df.dropna(subset=["startdate_action", "enddate_action", "geographic_level", "location", "action"], how="any")

    # convert columns to datetime which contain datetime.
    df["startdate_action"] = pd.to_datetime(df["startdate_action"])
    df["enddate_action"] = pd.to_datetime(df["enddate_action"])
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    return df

def build_bar_chart_data():
    x = create_timeline() # the time line we want to show
    y = [randrange(10) for i in range(len(x))] # replace with actual cases
    data = go.Bar(
        x=x,
        y=y,
    )
    return data

def build_am_data():
    action_data = read_action_data()
    action_data  = action_data.sort_values("startdate_action")
    data = [go.Scatter(x=[action["startdate_action"], action["startdate_action"]+np.timedelta64(15, 'D')],
                       y=[row_num,row_num],
                       marker={"size": 16,
                              "symbol": "triangle-up",
                              "color":"green"},
                       mode="lines+markers+text",
                       text=["Anordnung - {0}".format(action["action"]), "mögl. Effekt"],

                       textposition="bottom center"
                       )
            for row_num, action in action_data.iterrows()]
    return data

# def create_action_marker_chart():
#     am_data = build_am_data()
#     am_layout = go.Layout(xaxis=dict(title="time", type="category"),
#                           yaxis=dict(title="measures", type="category"),
#                           showlegend=False)
#     am_fig = go.Figure(data=am_data, layout=am_layout)
#     am_chart = dcc.Graph(id='actions', figure=am_fig)
#     return am_chart

# def create_bar_chart():
#     bar_data = build_bar_chart_data()
#     count_days = len(bar_data.x)
#     focus = 16 #TODO make the zoom interactively
#     bar_layout = go.Layout(
#         xaxis=dict(type="category",range=[count_days-focus,count_days]) # range is the initial zoom on 16 days with the possibility to zoom out
#         ,yaxis=dict(title="Number of cases"))
#
#     bar_fig = go.Figure(data=bar_data, layout=bar_layout)
#     bar_fig.update_xaxes(tickangle=90)
#     bar_chart = dcc.Graph(id= 'Timeline', figure=bar_fig)
#     return bar_chart

def merge_figures():
    '''
    Merge the plots with add trace
    '''
    fig = go.Figure()
    am_figure = build_am_data()
    bar_figure = build_bar_chart_data()
    count_days = len(bar_figure.x)
    focus = 16 #TODO make the zoom interactively
    for am in am_figure:
        fig.add_trace(am)
    fig.add_trace(bar_figure)
    fig.update_xaxes(tickangle=90)
    fig.update_layout(
        xaxis=dict(type="category",range=[count_days-focus,count_days]) # range is the initial zoom on 16 days with the possibility to zoom out
        ,yaxis=dict(title="Number of cases"))
    graph = dcc.Graph(id= 'Timeline', figure=fig)
    return graph


def normalize_data():
    '''
    normalize the data with population
    :return:
    '''

# bar_chart = create_bar_chart()
# am_chart = create_action_marker_chart()
plot = merge_figures()

app.layout = html.Div(children=[
    html.H1(children='''
    Timeline of Events in Germany
    '''),
    # bar_chart,
    # am_chart
    plot

])

if __name__ == '__main__':
    print('reload')
    app.run_server(host="0.0.0.0", debug=True)
