# -*- coding: utf-8 -*-
import itertools
import json

import dash
import plotly.graph_objects as go
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
# Needed for gunicorn
server = app.server

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
    fig.layout['uirevision'] = 'x'

    return fig


def create_bar():
    years = [1995, 1996, 1997, 1998, 1999, 2000, 2001, 2002, 2003,
             2004, 2005, 2006, 2007, 2008, 2009, 2010, 2011, 2012]

    fig = go.Figure()
    fig.add_trace(go.Bar(x=years,
                         y=[219, 146, 112, 127, 124, 180, 236, 207, 236, 263,
                            350, 430, 474, 526, 488, 537, 500, 439],
                         name='Rest of world',
                         marker_color='rgb(55, 83, 109)'
                         ))
    fig.add_trace(go.Bar(x=years,
                         y=[16, 13, 10, 11, 28, 37, 43, 55, 56, 88, 105, 156, 270,
                            299, 340, 403, 549, 499],
                         name='China',
                         marker_color='rgb(26, 118, 255)'
                         ))

    fig.update_layout(
        title='US Export of Plastic Scrap',
        xaxis_tickfont_size=14,
        yaxis=dict(
            title='USD (millions)',
            titlefont_size=16,
            tickfont_size=14,
        ),
        legend=dict(
            x=0,
            y=1.0,
            bgcolor='rgba(255, 255, 255, 0)',
            bordercolor='rgba(255, 255, 255, 0)'
        ),
        barmode='group',
        bargap=0.15,  # gap between bars of adjacent location coordinates.
        bargroupgap=0.1  # gap between bars of the same location coordinate.
    )
    return fig


app.layout = html.Div(children=[
    html.Div(children=[
        daq.ToggleSwitch(
            id='county-country-switch',
            label='Landkreis/Bundesland',
            labelPosition='bottom'
        ),
        dcc.Graph(
            id='map',
            figure=create_figure(False)
        ),
        html.Div(id='click-data')
    ], style={'width': '50%', 'float': 'left'}),
    html.Div(children=[
        dcc.Graph(
            id='bar',
            figure=create_bar()
        )
    ], style={'width': '50%', 'float': 'right'}),
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
