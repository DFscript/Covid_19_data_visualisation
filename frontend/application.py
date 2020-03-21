# -*- coding: utf-8 -*-
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
    germany = create_germany()
    return germany


app.layout = html.Div(children=[
    dcc.Graph(
        id='example-graph',
        figure=create_figure()
    )
])

if __name__ == '__main__':
    app.run_server(host="0.0.0.0", debug=True)
