# -*- coding: utf-8 -*-
import json
import os

import numpy as np
import dash
import dash_core_components as dcc
import dash_html_components as html
import plotly.express as px
import pandas as pd

from germany import create_germany

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
app.scripts.config.serve_locally=True


def create_figure():
    with open('./county_centers/landkreise_marker.json') as json_file:
        county_to_middles = json.load(json_file)

    with open('../data-cases/RKI_COVID19.geojson') as json_file:
        data_cases = json.load(json_file)

    elements_to_remove = []
    case_list = []
    for element in data_cases['features']:
        props = element['properties']
        county_id = props['IdLandkreis']

        if county_id not in county_to_middles:
            print("We have no geocoords for:", county_id, "therefore throwing out")
            elements_to_remove.append(element)
        else:
            case_list.append(props)

    rows = []
    for index, case in enumerate(case_list):
        county = case['Landkreis']
        country = case['Bundesland']
        lat, lon = tuple(county_to_middles[case['IdLandkreis']])
        infected = case['AnzahlFall']
        timestamp = case['Meldedatum']
        deaths = case['AnzahlTodesfall']
        rows.append([country, county, lat, lon, infected, timestamp, deaths])

    df = pd.DataFrame(data=rows, columns=['country', 'county', 'lat', 'lon', 'infected', 'timestamp', 'deaths'])
    # df['timestamp'] = pd.to_datetime(df['timestamp'])
    # Make it so that ('county', 'timestamp') are unique and sum up deaths and infected while doing so
    df = df.groupby(by=['timestamp', 'county', 'lat', 'lon', 'country'])[['deaths', 'infected']].sum().reset_index().\
        sort_values(by=['county', 'timestamp'], ascending=[True, True])
    # df.to_csv('data_set.csv', index=False)

    df[['deaths', 'infected']] = df.groupby(by=['county'])[['deaths', 'infected']].cumsum()

    # df.to_csv('data_set_accumulated.csv', index=False)

    df = df.sort_values(by=['county', 'timestamp'], ascending=[True, False])

    # Cut off time
    df['timestamp'] = df['timestamp'].str.split('T').str[0]

    df = df.sort_values(by='timestamp')

    fig = px.scatter_mapbox(df, lat='lat', lon='lon', size="infected", mapbox_style='open-street-map',
                            animation_frame='timestamp', height=800)
    # fig = px.scatter_geo(df, hover_name="county", size="infected", animation_frame="timestamp",
    #                      projection="natural earth")

    return fig


app.layout = html.Div(children=[
    dcc.Graph(
        id='example-graph',
        figure=create_figure()
    )
])

if __name__ == '__main__':
    app.run_server(host="0.0.0.0", debug=True)
