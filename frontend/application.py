# -*- coding: utf-8 -*-
import json

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
    # germany = create_germany()
    # Acquire countries
    # import urllib.request, json
    # with urllib.request.urlopen("http://maps.googleapis.com/maps/api/geocode/json?address=google") as url:
    #     data = json.loads(url.read().decode())
    #     print(data)

    # Load cases
    with open('../data-cases/RKI_COVID19.geojson') as json_file:
        data = json.load(json_file)
        print(data)

    import plotly.express as px
    df = px.data.gapminder()
    fig = px.scatter_geo(df, locations="iso_alpha", color="continent",
                         hover_name="country", size="pop",
                         animation_frame="year",
                         projection="natural earth")
    return fig


app.layout = html.Div(children=[
    dcc.Graph(
        id='example-graph',
        figure=create_figure()
    )
])

if __name__ == '__main__':
    app.run_server(host="0.0.0.0", debug=True)
