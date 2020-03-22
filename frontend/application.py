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
from textwrap import dedent
help_text = """
# Willkommen bei Causality vc. Corona.

Der Corona-Viruas breitet sich über Deutschland, Europa und global aus und Regierungen auf der ganzen Welt suchen und erlassen Maßnahmen mit dem Ziel die Ausbreitung des Viruses zu verlangsamen. Nicht nur auf der Ebene von Nationen sonder auf allen Ebenen bis hinunter zu zu Städten und Kreisen rätseln, welche Maßnahmen am effektivsten sind.

Um diese Frage letztlich zu beantworten muss man sich ansehen, wie sich der Verlauf der Infektionszahlen im Nachgang zu verschiedenen Maßnahmen verhalten. Beim Corona-Virus geht man typischerweise davon aus, dass sich die Effekte von getroffenen Maßnahmen nicht vor dem 15ten Tag nach Inkraftreten der Maßnahme sichtbar werden.

## Das CausalityVsCorona-Projekt

Das Decisive Actions Team, dass sich im Rahmen des #WeVsVirusHack zusammengefunden hat, hat Maßnahmen recherchiert, die auf verschiedenen Ebenen getroffen worden sind und diese zusammen mit den Infektionszahlen in der betreffenden Region/dem Bundeslang zusammengebracht.

## Die Darstellung

Der Verlauf der Infektionszahlen wird als Balkendiagramm dargestellt. Darüber werden die verschiedenen Maßnahmen dargestellt. Jede Maßnahme wird durch einen Marker zu ihrem Inkrafttreten, einer 15-tägigen, grau dargestellten Spanne in der noch keine Effekte zu erwarten sind und einer grün dargestellten Spanne vom 15ten Tag bis zu ihrem geplanten Ende repräsentiert. Der grün dargestellt Bereich erstreckt sich noch ein Stück über das Ende der Maßnahme hinaus, da es durchaus denkbar ist, dass eine Maßnahme auch nach ihrem Ende nachwirkt.

Diese Darstellung kann z.Zt. für jedes der Bundesländer aus der Deutschlandkarte ausgewählt werden. Später ist eine Auflösung bis auf Kreisebene geplant.

## Weiterentwicklung

Das Projekt soll auch nach dem Ende des Hackathons weiterentwickelt werden. Zurzeit sind folgende Erweiterungen geplant:

*   Auflösung bis auf Kreis-Ebene
*   Erweiterung über Deutschland hinaus (Recherche-Teams gesucht)
"""

external_stylesheets = ['assets/external_stylesheet.css']
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
app.scripts.config.serve_locally = True
# Needed for gunicorn
server = app.server

def build_modal_info_overlay(id, side, content):
    """
    Build div representing the info overlay for a plot panel
    """
    div = html.Div([  # modal div
        html.Div([  # content div
            html.Div([
                html.H4([
                    "Info",
                    html.Img(
                        id=f'close-{id}-modal',
                        src="assets/close.png",
                        n_clicks=0,
                        className='info-icon',
                        style={'margin': 0},
                    ),
                ], className="container_title", style={'color': 'white'}),

                dcc.Markdown(
                    content
                ),
            ])
        ],
            className=f'modal-content {side}',
        ),
        html.Div(className='modal')
    ],
        id=f"{id}-modal",
        style={"display": "none"},
    )

    return div

ZG_WINTER_HOLYDAYS = "Winterferien (regulär)"

def read_cases_data(acc_new):
    if acc_new == False:
        df_cases = pd.read_csv(r'../data-cases/data_set.csv')
        df_cases["timestamp"] = pd.to_datetime(df_cases["timestamp"])
    elif acc_new == True:
        df_cases = pd.read_csv(r'../data-cases/data_set_accumulated.csv')
        df_cases["timestamp"] = pd.to_datetime(df_cases["timestamp"])
    else:
        df_cases = pd.read_csv(r'../data-cases/data_set.csv')
        df_cases["timestamp"] = pd.to_datetime(df_cases["timestamp"])
    return df_cases


def read_event_data():
    df = pd.read_csv(r'../data-actions/Winterferien2019-20.csv')
    df["startdate_action"] = pd.to_datetime(df["startdate_action"], errors="coerce")
    df["enddate_action"] = pd.to_datetime(df["enddate_action"], errors="coerce")

    df = df.replace("Baden-Würtemberg", "Baden-Württemberg")
    df = df.replace("Mecklenburg Vorpommern", "Mecklenburg-Vorpommern")
    df = df.replace("NRW", "Nordrhein-Westfalen")

    df = df.dropna(subset=["startdate_action", "enddate_action", "location"], how="any")
    return df


def read_action_data():
    df = pd.read_csv(r'../data-actions/policymeasures - measures_taken.csv')

    # convert columns to datetime which contain datetime.
    df["startdate_action"] = pd.to_datetime(df["startdate_action"], errors="coerce")
    df["enddate_action"] = pd.to_datetime(df["enddate_action"], errors="coerce")
    df["enddate_action"] = df["enddate_action"].fillna(max(df["enddate_action"]))
    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
    df = df.replace("Baden-Würtemberg", "Baden-Württemberg")
    df = df.replace("Mecklenburg Vorpommern", "Mecklenburg-Vorpommern")
    df = df.replace("NRW", "Nordrhein-Westfalen")

    # Drop any row, which does not contain the bare minimum required for generating an action-marker.
    df = df.dropna(subset=["startdate_action", "enddate_action", "geographic_level", "location", "action"], how="any")
    return df


def create_timeline(df_cases, df_actions):
    # df_cases.index = df_cases['timestamp']
    df_cases.index = df_cases.index.tz_localize(None)
    if not df_actions["startdate_action"].empty and not df_cases.index.empty:
        earliest_date = min(min(df_cases.index), min(df_actions["startdate_action"]))
    elif not df_cases.index.empty:
        earliest_date = min(df_cases.index)
    elif not df_actions["startdate_action"].empty:
        earliest_date = min(df_actions["startdate_action"])

    if not df_actions["enddate_action"].empty:
        latest_date = max(max(df_cases.index), max(df_actions["enddate_action"]))
    elif not df_cases.index.empty:
        latest_date = max(df_cases.index)
    elif not df_actions["enddate_action"].empty:
        latest_date = max(df_actions["enddate_action"])

    start = earliest_date
    end = latest_date
    date_list = pd.DataFrame(pd.date_range(start=start, end=end))
    date_list.columns = ['Time']
    return date_list


df_cases = read_cases_data(acc_new=False)


def filter_data_set(country='Bayern', zielgruppe='Versammlungen', acc_new=False):
    df_cases = read_cases_data(acc_new=acc_new)
    df_actions = read_action_data()
    df_cases = df_cases[df_cases['country'] == country]
    df_cases = df_cases.groupby(['timestamp']).sum().tz_localize(None)

    df_actions = df_actions[df_actions['location'] == country]
    if type(zielgruppe) != list:
        zielgruppe = [zielgruppe]
    df_actions = df_actions[df_actions['Zielgruppe'].isin(zielgruppe)]
    return df_cases, df_actions


def build_merged_dataset(df_cases, timeline):
    # main idea if a timestamp is missing it is addded here
    timeline.index = timeline['Time']
    merged_df = timeline.join(df_cases, how='left')
    return merged_df


def build_bar_chart_data(df, log):
    bar_charts = []
    color = ['#3a1261']
    # for i,land in enumerate(['NRW','Bayern']): #option to implement multi select of countries
    x = df['Time']
    if log == True:
        y = df['infected']
    else:
        y = np.log(df['infected'])
    data = go.Bar(
        x=x,
        y=y,
        name='Bayern',
        marker_color=color[0]
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
        fracs.append(text[:next_space + 1])
        text = text[next_space + 1:]
    return "<br>".join(fracs)


def build_am_data(df_cases, action_data,log):
    # action_data = action_data.reindex(list(range(1,len(action_data)+1)))
    action_data.index = list(range(1, len(action_data) + 1))
    if not df_cases['infected'].empty:
        if log == False:
            max_cases = np.log(max(df_cases['infected'])) / len(action_data)
        elif log == True:
           max_cases = max(df_cases['infected']) / len(action_data)
    else:
        max_cases = len(action_data)

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
        x=[action["startdate_action"] + np.timedelta64(15, 'D'),
           action["startdate_action"] + np.timedelta64(15, 'D')],
        y=[max_cases * row_num, 0],
        mode="lines",
        line=dict(color="rgb(200,200,200)"),
    )
        for row_num, action in action_data.iterrows()
    ]

    # The actual action markers
    data += [go.Scatter(
        x=[action["startdate_action"], action["startdate_action"] + np.timedelta64(15, 'D')],
        y=[max_cases * row_num, max_cases * row_num],
        marker={"size": 16,
                "symbol": "triangle-down",
                "color": "rgb(220,220,220)"},
        mode="lines+markers",
        name="bla",  # action["action"],
        hovertemplate=am_hover_template.format(details_action=wrap_hover_text(action["details_action"]),
                                               start_date=action["startdate_action"].strftime("%d.%m.%Y"),
                                               end_date=action["enddate_action"].strftime("%d.%m.%Y")),
        # TODO: Evaluate what is possible with this template and what is impossible.
        text=[action["action"] + "<br> Beginn", ""],
        textposition="bottom center",
    )
        for row_num, action in action_data.iterrows()
    ]

    data += [go.Scatter(
        x=[action["startdate_action"] + np.timedelta64(15, 'D'),
           action["enddate_action"]],
        y=[max_cases * row_num, max_cases * row_num],
        marker={"size": 16,
                "symbol": "triangle-down",
                "color": "blue" if action["Zielgruppe"] == ZG_WINTER_HOLYDAYS else "green"},
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
        x=[action["startdate_action"] + np.timedelta64(15, 'D'),
           action["enddate_action"] + np.timedelta64(15, 'D')],
        y=[max_cases * row_num, max_cases * row_num],
        marker={"color": "blue" if action["Zielgruppe"] == ZG_WINTER_HOLYDAYS else "green"},
        mode="lines",
    )
        for row_num, action in action_data.iterrows() if action["enddate_action"]
    ]

    return data


def merge_figures(bar_figure, am_figure):
    '''
    Merge the plots with add trace
    '''
    fig = go.Figure()
    for am in am_figure:
        fig.add_trace(am)
    # for bar in bar_figure:

    for trace in fig['data']:
        if (trace['name'] == 'trace10'): trace['showlegend'] = False
    fig.add_trace(bar_figure[0])

    fig.update_xaxes(tickangle=90)
    fig.update_layout(
        showlegend=False,
        barmode='group',
        plot_bgcolor='white',
        xaxis=dict(
            # tickmode='linear',
            # range=[count_days-focus,count_days]
        ),  # range is the initial zoom on 16 days with the possibility to zoom out
        yaxis=dict(title="Number of new cases"))
    return fig


def main_figure(country, zielgruppe, acc_new=False,log = False):
    df_cases = read_cases_data(acc_new=acc_new)
    df_actions = read_action_data()

    df_events = read_event_data()

    df_events["Zielgruppe"] = ZG_WINTER_HOLYDAYS
    df_events["action"] = "Winterferien"
    df_events["details_action"] = "Die regulären Winterferien des Bundeslandes."
    df_actions = pd.concat([df_actions, df_events])
    df_cases, df_actions = filter_data_set(country=country, zielgruppe=zielgruppe,
                                           acc_new=acc_new)  # filter on country level
    timeline = create_timeline(df_cases, df_actions)
    df_merged = build_merged_dataset(df_cases, timeline)
    bar_charts = build_bar_chart_data(df_merged, log)
    if not df_actions.empty:
        am_charts = build_am_data(df_cases, df_actions,log)
    else:
        am_charts = []
    figure = merge_figures(bar_charts, am_charts)
    return figure


def normalize_data():
    '''
    normalize the data with population
    :return:
    '''


df_actions = read_action_data()
relevant_countries1 = df_cases["country"].to_list()
relevant_countries2 = df_actions["location"].to_list()
relevant_countries = np.unique(relevant_countries1 + relevant_countries2)
relevant_countries = [rel_c for rel_c in relevant_countries if rel_c != 'Berlin']
relevant_countries = [rel_c.strip() for rel_c in relevant_countries]

df_zielgruppe = df_actions["Zielgruppe"].dropna().unique()


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
    df = df.groupby(by=['timestamp', 'county', 'lat', 'lon', 'country'])[['deaths', 'infected']].sum().reset_index(). \
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

        fig = px.scatter_mapbox(df, lat='lat', lon='lon', size="infected", size_max=60, mapbox_style='open-street-map',
                                animation_frame='timestamp', height=800, hover_data=['country', 'infected', 'deaths'],
                                custom_data=['country'])

    if bubble_for_each_county:
        # Needed to have time slider values sorted
        df = df.sort_values(by='timestamp')

        fig = px.scatter_mapbox(df, lat='lat', lon='lon', size="infected", mapbox_style='open-street-map',
                                animation_frame='timestamp', height=800, hover_data=['country', 'county', 'infected',
                                                                                     'deaths'],
                                custom_data=['country', 'county'])
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
    options=[{
        "label": i,
        "value": i
    } for i in relevant_countries],
    value='Bayern',
    # multi=True
)

dropdown_zielgruppe = dcc.Dropdown(
    id='zielgruppe',
    options=[{
        "label": i,
        "value": i
    } for i in df_zielgruppe],
    value='Versammlungen',
    multi=True
)

select_all = dcc.Checklist(id='select-all',
                           options=[{'label': 'Select All', 'value': "1"}])

fig = main_figure(country="Bayern", zielgruppe="Versammlungen")
plot = dcc.Graph(id='Timeline', figure=fig)

accumulated_new_switch = daq.ToggleSwitch(
    id='accumulated_new_switch',
    label='new infected / accumulated',
    labelPosition='bottom'
)

log_lin_switch = daq.ToggleSwitch(
    id='log_lin_switch',
    label='log / linear',
    labelPosition='bottom',
    value = False
)

app.layout = html.Div(id="container", children=[
    html.Div(id="container_left", children=[
        build_modal_info_overlay('indicator', 'bottom', dedent(help_text)),
        html.Img(
                        id='show-indicator-modal',
                        src="assets/question.png",
                        n_clicks=0,
                        className='info-icon',
                    ),
        html.H1(children='''
            Spatial overview
            ''', id='header2'),
        daq.ToggleSwitch(
            id='county-country-switch',
            label='Bundesland/Landkreis',
            labelPosition='bottom'
        ),
        dcc.Graph(
            id='map',
            figure=create_figure(False)
        ),
        html.Div(id='click-data')
    ]),

    html.Div(id="container_right", children=[

        html.H1(children='''
            Timeline of Events in Germany
            ''', id='header'),
        dropdown_bundesland,
        dropdown_zielgruppe,
        select_all,
        plot,html.Div(children =[
        accumulated_new_switch,log_lin_switch])

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
               Input("zielgruppe", "value"),
               Input("select-all", "value"),
               Input("zielgruppe", "options"),
               Input("accumulated_new_switch", "value"),
               Input("log_lin_switch","value")
               ])
def filter_plot(bundesland, zielgruppe, select_all, all_zielgruppe, acc_new,log):
    if select_all == ["1"]:
        all_zielgruppe = [i['value'] for i in all_zielgruppe]
        figure = main_figure(country=bundesland, zielgruppe=all_zielgruppe, acc_new=acc_new,log =log)
    else:
        figure = main_figure(country=bundesland, zielgruppe=zielgruppe, acc_new=acc_new,log=log)

    return figure


@app.callback([Output(f"indicator-modal", 'style'), Output(f"container_left", 'style')],
                      [Input(f'show-indicator-modal', 'n_clicks'),
                       Input(f'close-indicator-modal', 'n_clicks')])
def toggle_modal(n_show, n_close):
    ctx = dash.callback_context
    if ctx.triggered and ctx.triggered[0]['prop_id'].startswith('show-'):
        return {"display": "block"}, {'zIndex': 1003}
    else:
        return {"display": "none"}, {'zIndex': 0}


if __name__ == '__main__':
    print('reload')
    app.run_server(host="0.0.0.0", debug=True)
