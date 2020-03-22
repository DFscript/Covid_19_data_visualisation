# -*- coding: utf-8 -*-
import dash
import dash_core_components as dcc
import dash_html_components as html
import pandas as pd
import numpy as np
import plotly.graph_objs as go
from dash.dependencies import Input, Output

external_stylesheets = ['assetes/external_sytlesheet.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

app.scripts.config.serve_locally=True

def read_cases_data():
    df_cases = pd.read_csv(r'data-cases/data_set.csv')
    df_cases["timestamp"] = pd.to_datetime(df_cases["timestamp"])
    return df_cases


def read_action_data():

    df = pd.read_csv(r'data-actions/policymeasures - measures_taken.csv')

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
    df_cases.index = df_cases['timestamp']
    df_cases.index = df_cases.index.tz_localize(None)
    earliest_date = min(min(df_cases.index),min(df_actions["startdate_action"]))
    latest_date = max(max(df_cases.index),max(df_actions["enddate_action"]))
    start = earliest_date
    end = latest_date
    date_list = pd.DataFrame(pd.date_range(start=start, end=end))
    date_list.columns = ['Time']
    return date_list


df_cases = read_cases_data()
df_actions = read_action_data()
timeline = create_timeline(df_cases.copy(),df_actions)

def filter_data_set_country_level(df_cases= df_cases,df_actions=df_actions,country = 'Bayern'):
    df_cases=df_cases[df_cases['country']==country]
    df_cases = df_cases.groupby(['timestamp']).sum().tz_localize(None)

    df_actions = df_actions[df_actions['location'] == country]
    # df_actions = df_actions[df_actions['action'] == 'Veranstaltungsverbot']
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
                            "color":"green"},
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
                    marker={"color":"green"},
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
            tickmode='linear',
                 # range=[count_days-focus,count_days]
        ), # range is the initial zoom on 16 days with the possibility to zoom out
        yaxis=dict(title="Number of new cases"))
    return fig



def main_figure(country):
    df_cases,df_actions = filter_data_set_country_level(country= country) # filter on country level
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


dropdown_bundesland = dcc.Dropdown(
        id='bundesland',
        options= [{
        "label": i,
        "value": i
    } for i in relevant_countries],
        value='Bayern',
    # multi=True
    )

fig = main_figure(country = "Bayern")
plot = dcc.Graph(id= 'Timeline', figure=fig)


app.layout = html.Div(children=[
    html.H1(children='''
    Timeline of Events in Germany
    ''',id = 'header'),
   dropdown_bundesland,
    plot

])


@app.callback(Output("Timeline", "figure"),
    [Input("bundesland", "value"),
    ],
)
def filter_plot(bundesland):
    figure = main_figure(country=bundesland)
    return figure

if __name__ == '__main__':
    print('reload')
    app.run_server(host="0.0.0.0", debug=True)


