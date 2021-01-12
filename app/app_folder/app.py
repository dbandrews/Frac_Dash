import dash
import dash
import dash_core_components as dcc
import dash_html_components as html
import dash_table as dt
import pandas as pd
import numpy as np
import plotly.graph_objs as go
import base64
import io
import json
import flask as flask
from dash.dependencies import Input,Output,State
#import flask server and app 
from .server import app,server

#Import callbacks and layouts for each tab from separate files
from . import app_detail
from . import app_teaser

app.title = 'Frac Dash'

# #suppress errors from returning layout before callbacks defined
#app.config['suppress_callback_exceptions'] =True

# df = pd.read_csv('app_folder\\df_by_well.csv')
# df_total = pd.read_csv('app_folder\\df_total.csv')



app.layout = html.Div([
        html.Div(
            [
                    html.H1(
                    children='Frac Dash',
                    className='four columns',
                    style={'color':'#FFFFFF','font-style':'italic','margin-left':'10px'}
                ),
                html.A(
                    html.H5(
                        children='By: Oakridge Analytics',
                        #className='four columns',
                        style={
                            'float': 'right',
                            'position': 'relative',
                            'margin-right':'10px',
                            'color':'#FFFFFF'
                        }
                    ), href='mailto:info@fracdash.com'
                )
            ],
            className='row',
            style = {
                'background-color':'#2C4081',
            }
    ),
    html.Div([
        dcc.Tabs(id="tab_selector",parent_className='custom-tabs',
        className='custom-tabs-container', value='teaser', children=[
            dcc.Tab(label='Teaser View', value='teaser',
                className='custom-tab',
                selected_className='custom-tab--selected'),
            dcc.Tab(label='Detail View', value='detail',
                className='custom-tab',
                selected_className='custom-tab--selected')
        ]),
        html.Div(id='tabs-content-example'),
        html.Div(dt.DataTable(data=[{}]), style={'display': 'none'})
    ],style={'margin':'0px 5px 5px 5px'})
])

@app.callback(Output('tabs-content-example','children'),
[Input('tab_selector','value')])
def return_tab_content(selected_tab):
    if selected_tab == 'teaser':
        return app_teaser.layout
    elif selected_tab == 'detail':
        return app_detail.layout


#FOR OFFLINE USE THE FOLLOWING
# app.css.config.serve_locally = True
# app.scripts.config.serve_locally = True



