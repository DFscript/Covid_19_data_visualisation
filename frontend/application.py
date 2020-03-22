# -*- coding: utf-8 -*-
import itertools
import json

import dash
import dash_core_components as dcc
import dash_daq as daq
import dash_html_components as html
import pandas as pd
import plotly.express as px
from dash.dependencies import Input
from dash.dependencies import Output

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
app.scripts.config.serve_locally = True


def create_figure(bubble_for_each_county):
    with open('./county_centers/bundeslaender_marker.json') as json_file:
        country_to_middles = json.load(json_file)

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
    county_day_map = {}
    county_to_country_lat_lon = {}
    for index, case in enumerate(case_list):
        county = case['Landkreis']
        country = case['Bundesland']
        lat, lon = tuple(county_to_middles[case['IdLandkreis']])
        infected = case['AnzahlFall']
        timestamp = case['Meldedatum']
        deaths = case['AnzahlTodesfall']
        row = [county, country, lat, lon, timestamp, infected, deaths]
        rows.append(row)
        county_day_map[(county, timestamp)] = row
        if county not in county_to_country_lat_lon:
            county_to_country_lat_lon[county] = [country, lat, lon]

    df_uncompleted = pd.DataFrame(data=rows,
                                  columns=['county', 'country', 'lat', 'lon', 'timestamp', 'infected', 'deaths'])

    unique_days = df_uncompleted['timestamp'].unique()
    unique_days.sort()
    unique_counties = df_uncompleted['county'].unique()
    unique_counties.sort()

    full_matrix = []
    for day, county in itertools.product(unique_days, unique_counties):
        if (county, day) in county_day_map:
            full_matrix.append(county_day_map[(county, day)])
        else:
            full_matrix.append([county] + county_to_country_lat_lon[county] + [day] + [0, 0])

    df = pd.DataFrame(data=full_matrix,
                      columns=['county', 'country', 'lat', 'lon', 'timestamp', 'infected', 'deaths'])

    df = df.sort_values(by=['county', 'timestamp'], ascending=[True, True])
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

    if not bubble_for_each_county:
        df = df.groupby(by=['country', 'lat', 'lon', 'timestamp'])[['infected', 'deaths']].sum().reset_index()
        middles = df['country'].map(lambda x: country_to_middles[x])
        new_lat_lon = pd.DataFrame()
        new_lat_lon['lat'] = middles.map(lambda x: x[0])
        new_lat_lon['lon'] = middles.map(lambda x: x[1])
        df[['lat', 'lon']] = new_lat_lon
        # Needed to have time slider values sorted
        df = df.sort_values(by='timestamp')

        fig = px.scatter_mapbox(df, lat='lat', lon='lon', size="infected", mapbox_style='open-street-map',
                                animation_frame='timestamp', height=800, hover_data=['country', 'infected', 'deaths'],
                                custom_data=['country'])

    if bubble_for_each_county:
        # Needed to have time slider values sorted
        df = df.sort_values(by='timestamp')

        fig = px.scatter_mapbox(df, lat='lat', lon='lon', size="infected", mapbox_style='open-street-map',
                                animation_frame='timestamp', height=800, hover_data=['county', 'infected', 'deaths'],
                                custom_data=['county', 'country'])
    # fig = px.scatter_geo(df, hover_name="county", size="infected", animation_frame="timestamp",
    #                      projection="natural earth")

    fig.layout['clickmode'] = 'event+select'

    return fig


app.layout = html.Div(children=[
    daq.ToggleSwitch(
        id='county-country-switch',
        label='County/Country',
        labelPosition='bottom'
    ),
    dcc.Graph(
        id='map',
        figure=create_figure(False)
    ),
    html.Div(id='click-data')
])


@app.callback(
    Output('click-data', 'children'),
    [Input('map', 'clickData')])
def display_click_data(click_data):
    return json.dumps(click_data, indent=2)


@app.callback(
    dash.dependencies.Output('map', 'figure'),
    [dash.dependencies.Input('county-country-switch', 'value')])
def update_output(value):
    if value is None:
        return dash.no_update
    else:
        return create_figure(value)


if __name__ == '__main__':
    app.run_server(host="0.0.0.0", debug=True)
