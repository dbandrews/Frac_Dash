from flask import Flask
from dash import Dash

server = Flask('app_folder')
app = Dash(__name__,server=server)
app.config['suppress_callback_exceptions'] =True