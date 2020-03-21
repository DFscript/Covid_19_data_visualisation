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
        county_id = case['IdLandkreis']
        lat, lon = tuple(county_to_middles[county_id])
        infected = case['AnzahlFall']
        timestamp = case['Meldedatum']
        deaths = case['AnzahlTodesfall']
        rows.append([county_id, lat, lon, infected, timestamp, deaths])

    df = pd.DataFrame(data=rows, columns=['county', 'lat', 'lon', 'infected', 'timestamp', 'deaths'])
    # df['timestamp'] = pd.to_datetime(df['timestamp'])

    # Cut off time
    df['timestamp'] = df['timestamp'].str.split('T').str[0]

    # Not quite sure but lat and lon where given in * 10e+6
    buf1 = df['lat'] * 1e-5
    buf2 = df['lon'] * 1e-5

    df['lat'] = buf2
    df['lon'] = buf1

    print(df['lat'])
    print(df['lon'])

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
