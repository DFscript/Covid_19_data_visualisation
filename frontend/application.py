# -*- coding: utf-8 -*-
import dash
import dash_core_components as dcc
import dash_html_components as html
import pandas as pd
import plotly.graph_objs as go



 
external_stylesheets = ['assetes/external_sytlesheet.css']
 
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
 
app.scripts.config.serve_locally=True

def clean_data(df):
    '''
    Clean the data e.g. drop na
    '''
    df =  df[df['timestamp'].notna()] #drop na in column timestamp
    return df

def read_data():
    '''
    load the data
    '''
    df_cases = clean_data(pd.read_csv('data-cases/RKI_Corona_Bundesländer.csv'))
    df_actions = clean_data(pd.read_csv('data-actions/policymeasures - measures_taken.csv'))
    return df_actions

def create_timeline():
    numdays = 8 #TODO make numdays interactive input
    date_list = pd.date_range(start='1/3/2020', periods=numdays)
    return date_list

def build_bar_chart_data():
    # df_actions = read_data()
    x = create_timeline() # the time line we want to show
    print(x)
    y = [3] * len(x)
    data = go.Bar(
        x=x,
        y=y,
    )

def create_bar_chart():
    bar_data = build_bar_chart_data()
    bar_layout = go.Layout(plot_bgcolor="#ffffff ",
                           yaxis=dict(title="Number of cases"))

    bar_fig = go.Figure(data=bar_data, layout=bar_layout)
    bar_chart = dcc.Graph(id="", figure=bar_fig)
    return bar_chart

def normalize_data():
    '''
    normalize the data with population
    :return:
    '''

bar_chart = create_bar_chart()

app.layout = html.Div(children=[
    html.H1(children='''
    Timeline of Events in Germany
    '''),
    bar_chart

])
 
if __name__ == '__main__':
    app.run_server(host="0.0.0.0", debug=True)
