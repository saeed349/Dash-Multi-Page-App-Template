import pandas as pd
from deltalake import DeltaTable
from plotly.offline import init_notebook_mode, iplot,plot
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.express as px

import warnings
import datetime
warnings.filterwarnings('ignore')

import dash
import dash_table
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State
import os


from app import app

df = None

layout = html.Div([
    html.Div(
        [
            html.Div([dcc.Dropdown(id='dropdown-symbols',
                 options=[{'label': i, 'value': i} for i in ['AAPL','MSFT']], multi=False, value="AAPL")],
            className='two columns'),
            html.Div([dcc.Slider(id='angle-slider',min=0, max=360,step=None,marks = {i:"{} deg".format(i) for i in range(0,360,30)},value=180)],
            className='two columns'),
            html.Div([dcc.RangeSlider(id='slope-slider',min=-45, max=45,step=None,marks = {i:"{}".format(i) for i in range(-45,46,1)},value=[-45,45])],
            className='two columns'),
            html.Div([dcc.Slider(id='distance-slider',min=0, max=100,step=None,marks = {i:"{} t".format(i) for i in range(0,100,10)},value=10)],
            className='two columns'),
            html.Div([dcc.Checklist(id='filter-dropdown',
                options=[
                    {'label': 'valid', 'value': 'valid'},
                    {'label': 'extended', 'value': 'extended'},
                    {'label': 'changed', 'value': 'changed'}
                ],
                value=['extended'],labelStyle={'display': 'inline-block'})],className='two columns'),
            html.Div([
                    dcc.DatePickerSingle(
                    id='date_picker',
                    date=str(datetime.datetime.now().date()))],
            className='four columns'),
    ],className='row'),    
    html.Br(),
    html.Div([
        dcc.Loading(id='loading-1',
        children=[html.Div(dcc.Graph(id="plot-candle-chart"))])
    ],style = {'display': 'inline-block', 'width': '100%','height':'200%'},className='row'),

    dcc.Link('Go back to home', href='/')
])
