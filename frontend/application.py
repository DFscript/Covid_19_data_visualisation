# -*- coding: utf-8 -*-
import dash
import dash_core_components as dcc
import dash_html_components as html
import pandas as pd
import plotly.graph_objs as go
import os


external_stylesheets = ['assetes/external_sytlesheet.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

app.scripts.config.serve_locally=True

def clean_data(df):
    '''
    Clean the data e.g. drop na
    '''
    df =  df[df['timestamp'].notna()] #drop na in column timestamp
    return df

# def read_data():
#     '''
#     load the data
#     '''
#     # df_cases = pd.read_csv(path_cases,sep = ',')
#     df_actions = clean_data(pd.read_csv(os.path.join("../data-actions", "policymeasures - measures_taken.csv")))
#     return df_actions

def create_timeline():
    numdays = 40 #TODO make numdays interactive input
    date_list = pd.date_range(start='3/1/2020', periods=numdays)
    date_list =[str(date)[:10] for date in date_list]
    return date_list

def build_bar_chart_data():
    # df_actions= read_data()
    x = create_timeline() # the time line we want to show
    print(x)
    y = [3] * len(x)
    data = go.Bar(
        x=x,
        y=y,
    )
    return data

def build_am_data():
    data = [go.Scatter(x=[i*2+0,i*2+16], y=[-i,-i],
                      marker={"size": 32,
                            "symbol": "triangle-up"},
                      mode="lines+markers+text",
                      name="Kinos schließen",
                      text=["Anordnung Kinos schließen", "mögl. Effekt"],

                      textposition="bottom center"
                      )
            for i in range(5)]
    return data

def create_action_marker_chart():
    am_data = build_am_data()
    am_layout = go.Layout(xaxis=dict(title="measures", type="category"),
                          yaxis=dict(title="time", type="category"))
    am_figure = go.Figure(data=am_data, layout=am_layout)
    am_chart = dcc.Graph(id='actions', figure=am_figure)
    return am_chart

def create_bar_chart():
    bar_data = build_bar_chart_data()
    count_days = len(bar_data.x)
    focus = 16
    bar_layout = go.Layout(
        xaxis=dict(type="category",range=[count_days-focus,count_days]) # range is the initial zoom on 16 days with the possibility to zoom out
        ,yaxis=dict(title="Number of cases"))

    bar_fig = go.Figure(data=bar_data, layout=bar_layout)
    bar_fig.update_xaxes(tickangle=90)
    bar_chart = dcc.Graph(id= 'Timeline', figure=bar_fig)
    return bar_chart

def normalize_data():
    '''
    normalize the data with population
    :return:
    '''

bar_chart = create_bar_chart()
am_chart = create_action_marker_chart()

app.layout = html.Div(children=[
    html.H1(children='''
    Timeline of Events in Germany
    '''),
    bar_chart,
    am_chart

])

if __name__ == '__main__':
    print('reload')
    app.run_server(host="0.0.0.0", debug=True)
