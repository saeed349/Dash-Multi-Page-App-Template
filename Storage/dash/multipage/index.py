import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output

from app import app
from apps import app1, app2

app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    html.Div(id='page-content')
])

app.layout = html.Div([
    dcc.Link('Individual Analysis', href='/individual'),
    html.Br(),
    dcc.Link('Agregrate Analysis', href='/agregrate'),
])


@app.callback(Output('page-content', 'children'),
              [Input('url', 'pathname')])
def display_page(pathname):
    if pathname == '/individual':
        return app1.layout
    elif pathname == '/agregrate':
        return app2.layout
    else:
        return '404'



if __name__=="__main__":
    # app.run_server(debug=True, port=5001)
    app.run_server(
        host='0.0.0.0',
        port=8050,
        debug=True
    )