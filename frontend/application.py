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
    print(os.getcwd())
    with open('../data-cases/middles_per_county.json') as json_file:
        county_to_middles = json.load(json_file)

    with open('../data-cases/RKI_COVID19.geojson') as json_file:
        data_cases = json.load(json_file)

    elements_to_remove = []
    case_list = []
    for element in data_cases['features']:
        props = element['properties']
        county = props['Landkreis']

        if county not in county_to_middles:
            print("We have no geocoords for:", county, "therefore throwing out")
            elements_to_remove.append(element)
        else:
            case_list.append(props)

    rows = []
    for index, case in enumerate(case_list):
        county = case['Landkreis']
        lat, lon = tuple(county_to_middles[county])
        infected = case['AnzahlFall']
        timestamp = case['Meldedatum']
        deaths = case['AnzahlTodesfall']
        rows.append([county, lat, lon, infected, timestamp, deaths])

    df = pd.DataFrame(data=rows, columns=['county', 'lat', 'lon', 'infected', 'timestamp', 'deaths'])
    # df['timestamp'] = pd.to_datetime(df['timestamp'])

    # Cut off time
    df['timestamp'] = df['timestamp'].str.split('T').str[0]

    # Not quite sure but lat and lon where given in * 10e+6
    df['lat'] = df['lat'] * 10e-6
    df['lon'] = df['lon'] * 10e-6

    df_car = px.data.carshare()

    fig = px.scatter_mapbox(df, lat='lat', lon='lon', size="infected", mapbox_style='open-street-map',
                            animation_frame='timestamp')
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
