# -*- coding: utf-8 -*-
import itertools
import json

import dash
import plotly.graph_objects as go
import dash_core_components as dcc
import dash_daq as daq
import numpy as np
import dash_html_components as html
import pandas as pd
import plotly.express as px
from dash.dependencies import Input
from dash.dependencies import Output

external_stylesheets = ['assets/external_stylesheet.css']
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
app.scripts.config.serve_locally = True


def read_cases_data():
    df_cases = pd.read_csv(r'../data-cases/data_set.csv')
    df_cases["timestamp"] = pd.to_datetime(df_cases["timestamp"])
    return df_cases

def read_event_data():
    df = pd.read_csv(r'../data-actions/Winterferien2019-20.csv')
    df["startdate_action"] = pd.to_datetime(df["startdate_action"], errors="coerce")
    df["enddate_action"] = pd.to_datetime(df["enddate_action"], errors="coerce")


    df = df.replace("Baden-Würtemberg","Baden-Württemberg")
    df = df.replace("Mecklenburg Vorpommern","Mecklenburg-Vorpommern")
    df = df.replace("NRW","Nordrhein-Westfalen")

    df = df.dropna(subset=["startdate_action", "enddate_action",  "location"], how="any")
    return df

def read_action_data():

    df = pd.read_csv(r'../data-actions/policymeasures - measures_taken.csv')

    # convert columns to datetime which contain datetime.
    df["startdate_action"] = pd.to_datetime(df["startdate_action"], errors="coerce")
    df["enddate_action"] = pd.to_datetime(df["enddate_action"], errors="coerce")
    df["enddate_action"] = df["enddate_action"].fillna(max(df["enddate_action"]))
    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
    df = df.replace("Baden-Würtemberg","Baden-Württemberg")
    df = df.replace("Mecklenburg Vorpommern","Mecklenburg-Vorpommern")
    df = df.replace("NRW","Nordrhein-Westfalen")


    # Drop any row, which does not contain the bare minimum required for generating an action-marker.
    df = df.dropna(subset=["startdate_action", "enddate_action", "geographic_level", "location", "action"], how="any")
    return df



def create_timeline(df_cases,df_actions):
    # df_cases.index = df_cases['timestamp']
    df_cases.index = df_cases.index.tz_localize(None)
    if not df_actions["startdate_action"].empty and not df_cases.index.empty:
        earliest_date = min(min(df_cases.index),min(df_actions["startdate_action"]))
    elif not df_cases.index.empty:
        earliest_date = min(df_cases.index)
    elif not df_actions["startdate_action"].empty:
        earliest_date = min(df_actions["startdate_action"])


    if not df_actions["enddate_action"].empty:
        latest_date = max(max(df_cases.index),max(df_actions["enddate_action"]))
    elif not df_cases.index.empty:
        latest_date = max(df_cases.index)
    elif not df_actions["enddate_action"].empty:
        latest_date =max(df_actions["enddate_action"])
    start = earliest_date
    end = latest_date
    date_list = pd.DataFrame(pd.date_range(start=start, end=end))
    date_list.columns = ['Time']
    return date_list


df_actions = read_action_data()



df_events = read_event_data()
ZG_WINTER_HOLYDAYS = "Winterferien (regulär)"
df_events["Zielgruppe"] = ZG_WINTER_HOLYDAYS
df_events["action"] = "Winterferien"
df_events["details_action"] = "Die regulären Winterferien des Bundeslandes."
df_actions = pd.concat([df_actions, df_events])


def filter_data_set(df_cases= df_cases,df_actions=df_actions,country = 'Bayern',zielgruppe = 'Versammlungen'):
    df_cases=df_cases[df_cases['country']==country]
    df_cases = df_cases.groupby(['timestamp']).sum().tz_localize(None)

    df_actions = df_actions[df_actions['location'] == country]
    if type(zielgruppe) !=list:
        zielgruppe = [zielgruppe]
    df_actions = df_actions[df_actions['Zielgruppe'].isin(zielgruppe)]
    return df_cases,df_actions

def build_merged_dataset(df_cases,timeline):
    #main idea if a timestamp is missing it is addded here
    timeline.index = timeline['Time']
    merged_df = timeline.join(df_cases,how='left')
    return merged_df


def build_bar_chart_data(df):
    bar_charts =[]
    color = ['#474747','#B3B3B3']
    # for i,land in enumerate(['NRW','Bayern']):
    x= df['Time']
    y = df['infected']
    data = go.Bar(
        x=x,
        y=y,
        name = 'Bayern',
        marker_color = color[0]
    )
    bar_charts.append(data)
    return bar_charts

am_hover_template = """
<b>%{{text}}</b><br>
{details_action} <br><br>
<i>Vom {start_date} bis vorauss. {end_date}</i>
<extra></extra>
"""

def wrap_hover_text(text):
    if type(text) is not str:
        return text
    fracs = []
    while len(text) > 0:
        next_space = text.find(" ", 80)  # at least 80 chars per line (expect last line).
        if next_space == -1:
            fracs.append(text)
            break
        fracs.append(text[:next_space+1])
        text = text[next_space+1:]
    return "<br>".join(fracs)



def build_am_data(df_cases,action_data):
    #action_data = action_data.reindex(list(range(1,len(action_data)+1)))
    action_data.index = list(range(1, len(action_data) + 1))
    if not df_cases['infected'].empty:
        max_cases = max(df_cases['infected']) / len(action_data)
    else:
        max_cases=  len(action_data)


    action_data = action_data.sort_values("startdate_action")

    # grey lines at start of the action.
    data = [go.Scatter(
                x=[action["startdate_action"], action["startdate_action"]],
                y=[max_cases * row_num, 0],
                mode="lines",
                line=dict(color="rgb(200,200,200)"),
                )
                for row_num, action in action_data.iterrows()
            ]
    # grey lines at point of effect of the action.
    data += [go.Scatter(
                x=[action["startdate_action"]+np.timedelta64(15, 'D'),
                  action["startdate_action"]+np.timedelta64(15, 'D')],
                y=[max_cases * row_num, 0],
                mode="lines",
                line=dict(color="rgb(200,200,200)"),
                )
                for row_num, action in action_data.iterrows()
            ]


    # The actual action markers
    data += [go.Scatter(
                    x=[action["startdate_action"], action["startdate_action"]+np.timedelta64(15, 'D')],
                    y=[max_cases*row_num,max_cases*row_num],
                    marker={"size": 16,
                            "symbol": "triangle-down",
                            "color":"rgb(220,220,220)"},
                    mode="lines+markers",
                    name="bla", #action["action"],
                    hovertemplate=am_hover_template.format(details_action=wrap_hover_text(action["details_action"]),
                                                           start_date=action["startdate_action"].strftime("%d.%m.%Y"),
                                                           end_date=action["enddate_action"].strftime("%d.%m.%Y")),
                                          #TODO: Evaluate what is possible with this template and what is impossible.
                    text=[action["action"] + "<br> Beginn", ""],
                    textposition="bottom center",
                    )
                for row_num, action in action_data.iterrows()
            ]

    data += [go.Scatter(
                    x=[action["startdate_action"]+np.timedelta64(15, 'D'),
                       action["enddate_action"]],
                    y=[max_cases*row_num,max_cases*row_num],
                    marker={"size": 16,
                            "symbol": "triangle-down",
                            "color":"blue" if action["Zielgruppe"] == ZG_WINTER_HOLYDAYS else "green"},
                    mode="lines+markers",
                    text=[action["action"] + "<br>mögl. Effekt", action["action"] + "<br>vorraus. Ende"],
                    textposition="bottom center",
                    hovertemplate=am_hover_template.format(details_action=wrap_hover_text(action["details_action"]),
                                               start_date=action["startdate_action"].strftime("%d.%m.%Y"),
                                               end_date=action["enddate_action"].strftime("%d.%m.%Y")),
                    # TODO: Evaluate what is possible with this template and what is impossible.
                    )
                for row_num, action in action_data.iterrows() if action["enddate_action"]
            ]
    data += [go.Scatter(
                    x=[action["startdate_action"]+np.timedelta64(15, 'D'),
                       action["enddate_action"]+np.timedelta64(15, 'D')],
                    y=[max_cases*row_num,max_cases*row_num],
                    marker={"color":"blue" if action["Zielgruppe"] == ZG_WINTER_HOLYDAYS else "green"},
                    mode="lines",
                    )
                for row_num, action in action_data.iterrows() if action["enddate_action"]
            ]

    return data

def merge_figures(bar_figure,am_figure):
    '''
    Merge the plots with add trace
    '''
    fig = go.Figure()
    for am in am_figure:
        fig.add_trace(am)
    # for bar in bar_figure:
    fig.add_trace(bar_figure[0])

    for trace in fig['data']:
        if (trace['name'] == 'trace10'): trace['showlegend'] = False

    fig.update_xaxes(tickangle=90)
    fig.update_layout(
        showlegend=False,
        barmode='group',
        plot_bgcolor ='white',
        xaxis=dict(
            # tickmode='linear',
                 # range=[count_days-focus,count_days]
        ), # range is the initial zoom on 16 days with the possibility to zoom out
        yaxis=dict(title="Number of new cases"))
    return fig



def main_figure(country,zielgruppe,df_cases=df_cases,df_actions=df_actions):
    df_cases,df_actions = filter_data_set(country= country,zielgruppe=zielgruppe) # filter on country level
    timeline = create_timeline(df_cases, df_actions)
    df_merged = build_merged_dataset(df_cases,timeline)
    bar_charts = build_bar_chart_data(df_merged)
    if not df_actions.empty:
        am_charts = build_am_data(df_cases,df_actions)
    else:
        am_charts = []
    figure = merge_figures(bar_charts,am_charts)
    return figure

def normalize_data():
    '''
    normalize the data with population
    :return:
    '''

relevant_countries1 = df_cases["country"].to_list()
relevant_countries2 = df_actions["location"].to_list()
relevant_countries = np.unique(relevant_countries1+relevant_countries2)
relevant_countries = [rel_c for rel_c in relevant_countries if rel_c != 'Niedersachsen']
df_zielgruppe =  df_actions["Zielgruppe"].dropna().unique()


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
                                animation_frame='timestamp', height=800, hover_data=['country', 'county', 'infected',
                                                                                     'deaths'],
                                custom_data=['county', 'country'])
    # fig = px.scatter_geo(df, hover_name="county", size="infected", animation_frame="timestamp",
    #                      projection="natural earth")

    fig.layout['clickmode'] = 'event+select'
    fig.layout['uirevision'] = 'x'

    return fig


# def create_bar():
#     years = [1995, 1996, 1997, 1998, 1999, 2000, 2001, 2002, 2003,
#              2004, 2005, 2006, 2007, 2008, 2009, 2010, 2011, 2012]
#
#     fig = go.Figure()
#     fig.add_trace(go.Bar(x=years,
#                          y=[219, 146, 112, 127, 124, 180, 236, 207, 236, 263,
#                             350, 430, 474, 526, 488, 537, 500, 439],
#                          name='Rest of world',
#                          marker_color='rgb(55, 83, 109)'
#                          ))
#     fig.add_trace(go.Bar(x=years,
#                          y=[16, 13, 10, 11, 28, 37, 43, 55, 56, 88, 105, 156, 270,
#                             299, 340, 403, 549, 499],
#                          name='China',
#                          marker_color='rgb(26, 118, 255)'
#                          ))
#
#     fig.update_layout(
#         title='US Export of Plastic Scrap',
#         xaxis_tickfont_size=14,
#         yaxis=dict(
#             title='USD (millions)',
#             titlefont_size=16,
#             tickfont_size=14,
#         ),
#         legend=dict(
#             x=0,
#             y=1.0,
#             bgcolor='rgba(255, 255, 255, 0)',
#             bordercolor='rgba(255, 255, 255, 0)'
#         ),
#         barmode='group',
#         bargap=0.15,  # gap between bars of adjacent location coordinates.
#         bargroupgap=0.1  # gap between bars of the same location coordinate.
#     )
#     return fig

dropdown_bundesland = dcc.Dropdown(
        id='bundesland',
        options= [{
        "label": i,
        "value": i
    } for i in relevant_countries],
        value='Bayern',
    # multi=True
    )

dropdown_zielgruppe = dcc.Dropdown(
        id='zielgruppe',
        options= [{
        "label": i,
        "value": i
    } for i in df_zielgruppe],
    value= 'Versammlungen',
    multi=True
    )

select_all = dcc.Checklist(id='select-all',
              options=[{'label': 'Select All', 'value': "1"}])

fig = main_figure(country="Bayern", zielgruppe="Versammlungen")
plot = dcc.Graph(id='Timeline', figure=fig)


app.layout = html.Div(id="container",children=[
    html.Div(id = "container_left",children=[
html.H1(children='''
            Spatial overview
            ''', id='header2'),
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
    ]),

    html.Div(id="container_right",children=[

            html.H1(children='''
            Timeline of Events in Germany
            ''', id='header'),
            dropdown_bundesland,
            dropdown_zielgruppe,
        select_all,
            plot
    ]),
])


@app.callback(
    Output('bundesland', 'value'),
    [Input('map', 'clickData')])
def display_click_data(click_data):
    if click_data is not None:
        return click_data['points'][0]['customdata'][0]
    else:
        return dash.no_update


@app.callback(
    dash.dependencies.Output('map', 'figure'),
    [dash.dependencies.Input('county-country-switch', 'value')])
def update_output(value):
    if value is None:
        return dash.no_update
    else:
        return create_figure(value)


@app.callback(Output("Timeline", "figure"),
              [Input("bundesland", "value"),
               Input("zielgruppe","value"),
               Input("select-all","value"),
            Input("zielgruppe","options"),
               ])
def filter_plot(bundesland, zielgruppe,select_all,all_zielgruppe):
    if select_all ==["1"]:
        all_zielgruppe = [i['value'] for i in all_zielgruppe]
        figure = main_figure(country=bundesland, zielgruppe=all_zielgruppe)
    else:
        figure = main_figure(country=bundesland, zielgruppe=zielgruppe)

    return figure


if __name__ == '__main__':
    print('reload')
    app.run_server(host="0.0.0.0", debug=True)


