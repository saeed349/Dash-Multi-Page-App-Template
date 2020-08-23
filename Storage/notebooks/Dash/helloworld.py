import jupyterlab_dash
import dash
import dash_html_components as html

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
from dash.exceptions import PreventUpdate
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# import flask

# import q_credentials.db_secmaster_cloud_cred as db_secmaster_cred
import q_credentials.db_secmaster_cred as db_secmaster_cred
import q_credentials.db_indicator_cred as db_indicator_cred

viewer = jupyterlab_dash.AppViewer()

external_stylesheets = ['https://codepen.io/amyoshino/pen/jzXypZ.css']
app = dash.Dash(
    __name__,
    external_stylesheets=external_stylesheets
)


# app.layout = dhc.Div([
#     dhc.Div([
#         dcc.Graph(id="plot-candle",figure=Currentfig)
#     ],style = {'display': 'inline-block', 'width': '100%','height':'200%'},className='row'),
#     dhc.Div(
#         [
#             dhc.Div([dcc.Dropdown(id='dropdown-securities',
#                     options=[{'label': i, 'value': i} for i in df_ticker_last_day['ticker'].unique()], multi=False, value="EUR_USD")],className='six columns')
# #             ,dhc.Div([dcc.Dropdown(id='dropdown-indicators',
# #                     multi=True,options=[{'label': i, 'value': i} for i in indicators])],className='six columns')
                     
#     ],className='row'),
# ])

params = [
    'Weight', 'Torque', 'Width', 'Height',
    'Efficiency', 'Power', 'Displacement'
]



app.layout = html.Div([
html.Div([
    dcc.Tabs(id="tabs-styled-with-props", value='tab-1', children=[
        dcc.Tab(label='1', value='tab-1'),
        dcc.Tab(label='2', value='tab-2'),
    ], colors={
        "border": "white",
        "primary": "gold",
        "background": "cornsilk"
    }),
    html.Div(id='tabs-content-props')
]),
# html.Div([
#     html.H1(children='Meta Data Dashboard',className='nine columns'),
#     html.Img(
#                     src="Images/jefdata.PNG",
#                     className='three columns',
#                     style={
#                         'height': '15%',
#                         'width': '15%',
#                         'float': 'right',
#                         'position': 'relative',
#                         'margin-top': 10,
#                     },
#                 ),
#                 html.Div(children='''
#                         Dash: A web application framework for Python.
#                         ''',
#                         className='nine columns'
#                 )
#     ],className='row'),
# html.Div([
#     html.Div([
#     dash_table.DataTable(
#         id='vendor_table',
#         columns=(
#             [{"name": i, "id": i} for i in df_vendor.columns]
#         ),
#         data = df_vendor.to_dict('records'),
#         editable=True,
# #         page_size=10,
# #         page_action='none',
#         style_table={'height': '400px', 'overflowY': 'auto'},
#         export_format='xlsx'
# #         export_headers='display',
# #         merge_duplicate_headers=True
#     )],className='twelve columns')
#     ],className='row'),
    
# html.Div([
#     html.Div([
#     dash_table.DataTable(
#         id='dataset_table',
#         columns=(
#             [{"name": i, "id": i} for i in df_dataset.columns]
#         ),
#         data = df_dataset.to_dict('records'),
#         editable=True,
# #         page_size=10,
# #         page_action='none',
#         style_table={'height': '400px', 'overflowY': 'auto'},
#         export_format='xlsx'
# #         export_headers='display',
# #         merge_duplicate_headers=True
#     )],className='twelve columns')
#     ],className='row'),
    
# html.Div([
#     html.Button('Save Data', id='save_file_button', n_clicks=0)
# ]),
# html.Div([
# dcc.Graph(id='table-editing-simple-output')
#     ],className='row'),

# html.Div([
# dcc.Graph(id='table-editing-simple-output2')
#     ],className='row'),
    
html.Div(id='hidden-div1', style={'display':'none'}),
html.Div(id='hidden-div2', style={'display':'none'})
])

@app.callback(Output('tabs-content-props', 'children'),
              [Input('tabs-styled-with-props', 'value')])
def render_content(tab):
    if tab == 'tab-1':
        return html.Div([
            html.H3('Tab content 1'),
            html.Div([
    html.H1(children='Meta Data Dashboard',className='nine columns'),
    html.Img(
                    src="Images/jefdata.PNG",
                    className='three columns',
                    style={
                        'height': '15%',
                        'width': '15%',
                        'float': 'right',
                        'position': 'relative',
                        'margin-top': 10,
                    },
                ),
                html.Div(children='''
                        Dash: A web application framework for Python.
                        ''',
                        className='nine columns'
                )
    ],className='row'),
html.Div([
    html.Div([
    dash_table.DataTable(
        id='vendor_table',
        columns=(
            [{"name": i, "id": i} for i in df_vendor.columns]
        ),
        data = df_vendor.to_dict('records'),
        editable=True,
#         page_size=10,
#         page_action='none',
        style_table={'height': '400px', 'overflowY': 'auto'},
        export_format='xlsx'
#         export_headers='display',
#         merge_duplicate_headers=True
    )],className='twelve columns')
    ],className='row'),
    
html.Div([
    html.Div([
    dash_table.DataTable(
        id='dataset_table',
        columns=(
            [{"name": i, "id": i} for i in df_dataset.columns]
        ),
        data = df_dataset.to_dict('records'),
        editable=True,
#         page_size=10,
#         page_action='none',
        style_table={'height': '400px', 'overflowY': 'auto'},
        export_format='xlsx'
#         export_headers='display',
#         merge_duplicate_headers=True
    )],className='twelve columns')
    ],className='row'),
    
html.Div([
    html.Button('Save Data', id='save_file_button', n_clicks=0)
]),
html.Div([
dcc.Graph(id='table-editing-simple-output')
    ],className='row'),
        ])
    elif tab == 'tab-2':
        return html.Div([
            html.H3('Tab content 2')
        ])

@app.callback(
#     Output('table-editing-simple-output', 'figure'),
    Output('hidden-div1','children'),
    [Input('save_file_button','n_clicks')],
    [State('vendor_table', 'data'),
     State('vendor_table', 'columns')])
def display_output(n_clicks,rows, columns):
    if n_clicks>0:
        df = pd.DataFrame(rows, columns=[c['name'] for c in columns])
        print("PODA")
        df.to_csv('Data/vendor.csv')
        raise PreventUpdate

@app.callback(
#     Output('table-editing-simple-output2', 'figure'),
    Output('hidden-div2','children'),
    [Input('save_file_button','n_clicks')],
    [State('dataset_table', 'data'),
     State('dataset_table', 'columns')])
def display_output_2(n_clicks, rows, columns):
    if n_clicks>0:
        df = pd.DataFrame(rows, columns=[c['name'] for c in columns])
        print("PODA")
    #     df.to_csv("Data/updated_dataset {}.csv".format(datetime.now().strftime("%m-%d-%Y-%H%M%S")))
        df.to_csv('Data/dataset.csv')
        raise PreventUpdate
