import psycopg2
import pandas as pd
from plotly.offline import init_notebook_mode, iplot
from plotly.offline import plot 
import plotly.graph_objects as go
import warnings
import datetime
warnings.filterwarnings('ignore')

import dash
import dash_table
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from app import app

df=pd.read_csv("/q_pack/data/AAPL.csv")
df=df[:200]

layout = html.Div([
    html.Div(
        [
            html.Div([dcc.Dropdown(id='dropdown-instrument',
                    options=[{'label': i, 'value': i} for i in df['instrument_type'].unique()], multi=False, value="Equity")],
            className='two columns'),
            html.Div([dcc.Dropdown(id='dropdown-securities',
                 options=[{'label': i, 'value': i} for i in ['']], multi=False, value="AAPL")],
            className='two columns'),
            html.Div([dcc.Dropdown(id='dropdown-timeframe',
                 options=[{'label': i, 'value': i} for i in ['m','w','d','h4','h1','test']], multi=False, value="d")],
            className='two columns'),
            html.Div([
                    dcc.DatePickerSingle(
                    id='date_picker',
                    date=str(datetime.datetime.now().date()))],
            className='four columns'),
    ],className='row'),    
    html.Br(),
    html.Div([
        dcc.Loading(id='loading-1',
        children=[html.Div(dcc.Graph(id="plot-candle"))])
    ],style = {'display': 'inline-block', 'width': '100%','height':'200%'},className='row'),

    dcc.Link('Go back to home', href='/')
])

@app.callback(
    Output('dropdown-securities', 'options'),
    [Input('dropdown-instrument', 'value')]
)
def update_tickerdropdown(instrument_type):
    return [{'label': i, 'value': i} for i in df['symbol'].unique()]

@app.callback(
    Output('plot-candle', 'figure'),
    [Input('dropdown-securities', 'value'),
    Input('dropdown-timeframe','value'),
    Input('date_picker', 'date')]
)
def updatePlot(symbol,timeframe,date):    
    data = [ dict( type = 'candlestick', open = df.open,high = df.high, low = df.low, close = df.close, x = df.index, yaxis = 'y1', name = 'price')]


    layout=dict()    
    layout['xaxis'] = dict( rangeslider = dict( visible = False ),autorange=True,fixedrange=False,visible=False,type='category')#type='category',
    layout['yaxis'] = dict( domain = [0.2, 1],autorange = True,fixedrange=False)
    layout['yaxis2'] = dict( domain = [0.0, 0.1],autorange = True,fixedrange=False)
    layout['yaxis3'] = dict( domain = [0.1, 0.2],autorange = True,fixedrange=False)
    # layout['shapes'] = level_plot(df,date)
    layout['margin']=dict(l=20, r=10)
    layout['paper_bgcolor']="LightSteelBlue"
    layout['width']=2200
    layout['height']=1000
    # to add the crosshair
    layout['xaxis']['showspikes']=True
    layout['xaxis']['spikemode']  = 'across'
    layout['xaxis']['spikesnap'] = 'cursor'
    fig = dict( data=data, layout=layout )
    return fig