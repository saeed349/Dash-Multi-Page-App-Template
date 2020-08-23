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

import q_credentials.db_secmaster_cred as db_secmaster_cred
import q_credentials.db_indicator_cred as db_indicator_cred
# import flask

# connect to our securities_master database
conn_secmaster = psycopg2.connect(host=db_secmaster_cred.dbHost , database=db_secmaster_cred.dbName, user=db_secmaster_cred.dbUser, password=db_secmaster_cred.dbPWD)
conn_indicator = psycopg2.connect(host=db_indicator_cred.dbHost , database=db_indicator_cred.dbName, user=db_indicator_cred.dbUser, password=db_indicator_cred.dbPWD)

sql="""SELECT s.ticker, max(d.symbol_id), max(d.date_price)
FROM public.symbol s inner join d_data d on s.id= d.symbol_id
group by s.ticker"""
df_ticker_last_day=pd.read_sql(sql,con=conn_secmaster)

def level_plot(df):
    support_ls = [[ls[0],ls[1],datetime.datetime.strptime(ls[2],'%Y-%m-%d %H:%M:%S'),ls[3]] for ls in df.iloc[-1]['level_support']]
    resistance_ls = [[ls[0],ls[1],datetime.datetime.strptime(ls[2],'%Y-%m-%d %H:%M:%S'),ls[3]] for ls in df.iloc[-1]['level_resistance']]
    end_dt=df.index[-1]
    res_plot_ls=[]
    sup_plot_ls=[]
    for res in resistance_ls[:5]:
        res_plot_ls.append(dict(x0=res[2],x1=end_dt,y0=res[0],y1=res[1],yref='y1',opacity=.2,fillcolor='Red',line=dict(color="black",width=1)))
    for sup in support_ls[:5]:
        sup_plot_ls.append(dict(x0=sup[2],x1=end_dt,y0=sup[0],y1=sup[1],yref='y1',opacity=.2,fillcolor='green',line=dict(color="black",width=1)))
    return (res_plot_ls+sup_plot_ls)

def data_selector(symbol_id):
    sql="select * from indicator"
    ind_list=list(pd.read_sql(sql,con=conn_indicator)['name'])
#     symbol_id='EUR_USD'#'AAPL'#'BOM500114'
    start_date=datetime.datetime(2018,1,1).strftime("%Y-%m-%d")
#     indicator_name = 'candle_1'
    
    sql="select d.date_price as date, open_price as open, high_price as high, low_price as low , close_price as close,volume from d_data d join symbol s on d.symbol_id = s.id where s.ticker='%s' and d.date_price > '%s'" %(symbol_id, start_date)
    df_price=pd.read_sql(sql,con=conn_secmaster)
    
    df_all_ind=pd.DataFrame()
    for ind in ind_list:
        print(ind)
        sql="select d.date_price as date, d.value from d_data d join symbol s on d.symbol_id = s.id join indicator i on i.id=d.indicator_id where s.ticker='%s' and i.name = '%s' and d.date_price > '%s'" %(symbol_id, ind, start_date)
        df_indicator=pd.read_sql(sql,con=conn_indicator)
        df_indicator.set_index('date',inplace=True)
        df_indicator=pd.concat([df_indicator.drop(['value'], axis=1), df_indicator['value'].apply(pd.Series)], axis=1)
        df_indicator.columns=[ind+"_"+col for col in df_indicator.columns]
        if df_all_ind.empty:
            df_all_ind=pd.merge(left=df_price, right=df_indicator,on='date')
        else:
            df_all_ind=pd.merge(left=df_all_ind, right=df_indicator,on='date')
    
    df_all_ind.set_index('date',inplace=True)
    return df_all_ind


# app = dash.Dash(__name__)

# app.layout = html.Div('Hello World Poda')

# viewer.show(app)
external_stylesheets = ['https://codepen.io/amyoshino/pen/jzXypZ.css']


# server = flask.Flask(__name__)
app = dash.Dash(
    __name__,
#     server=server,
    external_stylesheets=external_stylesheets
)


app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    html.Div(id='page-content')
])


index_page = html.Div([
    dcc.Link('Individual Analysis', href='/individual'),
    html.Br(),
    dcc.Link('Agregrate Analysis', href='/agregrate'),
])


page_individual_layout = html.Div([
    html.Div([
        dcc.Graph(id="plot-candle")#,figure=Currentfig
    ],style = {'display': 'inline-block', 'width': '100%','height':'200%'},className='row'),
    html.Div(
        [
            html.Div([dcc.Dropdown(id='dropdown-securities',
                    options=[{'label': i, 'value': i} for i in df_ticker_last_day['ticker'].unique()], multi=False, value="EUR_USD")],className='two columns')               
    ],className='row'),
    html.Br(),
    dcc.Link('Go back to home', href='/')
])

sql="select distinct instrument from symbol" # change it to exchange when you reload oanda
df_instrument_type=pd.read_sql(sql,con=conn_indicator)

sql="select * from indicator"
ind_list=list(pd.read_sql(sql,con=conn_indicator)['name'])
ind_list_id=list(pd.read_sql(sql,con=conn_indicator)['id'])

sql="select * from indicator"
df_ind_type=pd.read_sql(sql,con=conn_indicator)

page_agregrate_layout = html.Div([
    # html.Div([
    #     dcc.Graph(id="plot-candle")#,figure=Currentfig
    # ],style = {'display': 'inline-block', 'width': '100%','height':'200%'},className='row'),
    html.Div(
        [
            html.Div([dcc.Dropdown(id='dropdown-instrument',
                    options=[{'label': i, 'value': i} for i in df_instrument_type['instrument'].unique()], multi=False, value="Forex")],
            className='two columns'),
            html.Div([dcc.Dropdown(id='dropdown-indicator',
                    options=[{'label': row['name'], 'value': row['id']} for i,row in df_ind_type.iterrows()], multi=False, value="1")],
                    className='two columns'),
    ],className='row'),
    html.Div([
        html.Div([
        dash_table.DataTable(
            id='indicator_table',
            editable=False,
    #         page_size=10,
    #         page_action='none',
            style_table={'height': '400px', 'overflowY': 'auto'},
            # export_format='xlsx'
        )],className='twelve columns')
    ],className='row'),
    html.Br(),
    dcc.Link('Go back to home', href='/')
])

# @app.callback(dash.dependencies.Output('page-1-content', 'children'),
#               [dash.dependencies.Input('page-1-dropdown', 'value')])
# def page_1_dropdown(value):
#     sql="""SELECT max(s.id) as id, s.ticker, s.name, max(d.date_price) as date
#     FROM symbol s inner join d_data d on s.id= d.symbol_id where s.instrument='{}'
#     group by s.ticker,s.name""".format(selected_instrument)
#     df_symbols=pd.read_sql(sql,con=conn_indicator)
#     symbol_id=[str(i) for i in df_symbols['id']]
#     interested_date=(datetime.datetime.now().date()-datetime.timedelta(days=3)).strftime("%m-%d-%Y")
#     sql="select s.ticker, d.value, d.date_price as date from d_data d join symbol s on d.symbol_id=s.id where d.symbol_id in ({}) and d.indicator_id={} and date_price>'{}'".format((','.join(symbol_id))indicator,instrument)
#     df_indicator=pd.read_sql(sql,con=conn_indicator)
#     df_indicator=pd.concat([df_indicator.drop(['value'], axis=1), df_indicator['value'].apply(pd.Series)], axis=1)
#     columns=[{"name": i, "id": i} for i in df_indicator.columns]
#     data=df_indicator.to_dict('records')
#     return data,columns




@app.callback([Output('indicator_table', 'data'),
              Output('indicator_table', 'columns')],
              [Input('dropdown-indicator', 'value')],
              [State('dropdown-instrument', 'value')])
def indicator_dropdown(indicator,instrument):
    sql="""SELECT max(s.id) as id, s.ticker, s.name, max(d.date_price) as date
    FROM symbol s inner join d_data d on s.id= d.symbol_id where s.instrument='{}'
    group by s.ticker,s.name""".format(instrument)
    df_symbols=pd.read_sql(sql,con=conn_indicator)
    symbol_id=[str(i) for i in df_symbols['id']]
    interested_date=(datetime.datetime.now().date()-datetime.timedelta(days=3)).strftime("%m-%d-%Y")
    sql="select s.ticker, d.value, d.date_price as date from d_data d join symbol s on d.symbol_id=s.id where d.symbol_id in ({}) and d.indicator_id={} and date_price>'{}'".format((','.join(symbol_id)),indicator,interested_date)
    df_indicator=pd.read_sql(sql,con=conn_indicator)
    df_indicator=pd.concat([df_indicator.drop(['value'], axis=1), df_indicator['value'].apply(pd.Series)], axis=1)
    columns=[{"name": i, "id": i} for i in df_indicator.columns]
    data=df_indicator.to_dict('records')
    return data,columns

@app.callback(dash.dependencies.Output('page-2-content', 'children'),
              [dash.dependencies.Input('page-2-radios', 'value')])
def page_2_radios(value):
    return 'You have selected "{}"'.format(value)

# Update the index
@app.callback(dash.dependencies.Output('page-content', 'children'),
              [dash.dependencies.Input('url', 'pathname')])
def display_page(pathname):
    if pathname == '/individual':
        return page_individual_layout
    elif pathname == '/agregrate':
        return page_agregrate_layout
    else:
        return index_page


@app.callback(
    Output('plot-candle', 'figure'),
    [Input('dropdown-securities', 'value')]
)
def updatePlot(securityValue):
    
    interested_feature='anomaly_vol_anomaly'
    df=data_selector(securityValue)
    df_candle_1=df[-10:]
    df_candle_1=df_candle_1[df_candle_1['candle_1_pattern_name']!='']
    df_candle_1['pattern']='1'

    df_candle_2=df[-10:]
    df_candle_2=df_candle_2[df_candle_2['candle_2_pattern_name']!='']
    df_candle_2['pattern']='2'

    df_candle_3=df[-10:]
    df_candle_3=df_candle_3[df_candle_3['candle_3_pattern_name']!='']
    df_candle_3['pattern']='3'
    
    data = [ dict(
    type = 'candlestick',
    open = df.open,
    high = df.high,
    low = df.low,
    close = df.close,
    x = df.index,
    yaxis = 'y1',
    name = 'price'
    )]
    

    data.append( dict( x=df.index, y=df.volume,                         
                             marker=dict( color='blue' ),
                             type='bar', yaxis='y2', name='Volume'))

    data.append( dict( x=df.index, y=df[interested_feature],                         
                             marker=dict( color='red' ),
                             type='scatter', yaxis='y3', name=interested_feature))

    data.append( dict( x=df_candle_1.index, y=df_candle_1['high'],
                             text=df_candle_1['pattern'],
                             mode="markers+text",textfont_size=15,textposition="top center",
                             marker=dict( color='blue' ),
                             type='scatter', yaxis='y1', name='candle_patter_1'))

    data.append( dict( x=df_candle_2.index, y=df_candle_2['high'],
                             text=df_candle_2['pattern'],
                             mode="markers+text",textfont_size=15,textposition="top center",
                             marker=dict( color='red' ),
                             type='scatter', yaxis='y1', name='candle_patter_2'))


    data.append( dict( x=df_candle_3.index, y=df_candle_3['high'],
                             text=df_candle_3['pattern'],
                             mode="markers+text",textfont_size=15,textposition="top center",
                             marker=dict( color='red' ),
                             type='scatter', yaxis='y1', name='candle_patter_3'))


    layout=dict()    
    layout['xaxis'] = dict( rangeslider = dict( visible = False ),autorange=True,fixedrange=False,visible=False,type='category')#type='category',
    layout['yaxis'] = dict( domain = [0.2, 1],autorange = True,fixedrange=False)
    layout['yaxis2'] = dict( domain = [0.0, 0.1],autorange = True,fixedrange=False)
    layout['yaxis3'] = dict( domain = [0.1, 0.2],autorange = True,fixedrange=False)
    layout['shapes'] = level_plot(df)
    layout['margin']=dict(l=20, r=10)
    layout['paper_bgcolor']="LightSteelBlue"
    layout['width']=2200
    layout['height']=1000
    
    


    fig = dict( data=data, layout=layout )
    return fig


# @app.callback(
#     Output(component_id='plot_candle', component_property='figure'),
#     [Input('plot_candle', 'relayoutData')],
#     [State('plot_candle', 'figure')]
# )
# def update_output_div(input_value, fig):
#     fig['layout'] = {"title": "Poda Patti"}
#     print(input_value)
#     return fig


if __name__=="__main__":
    # app.run_server(debug=True, port=5001)
    app.run_server(
        host='0.0.0.0',
        port=8050,
        debug=True
    )