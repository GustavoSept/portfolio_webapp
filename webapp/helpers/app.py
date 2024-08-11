"""Helper functions related to the Flask app"""
import dash
import dash_bootstrap_components as dbc

def create_dash_app(server, routes_pathname_prefix, title, name):
    dash_app = dash.Dash(
        __name__,
        server=False,
        external_stylesheets=[dbc.themes.BOOTSTRAP],
        routes_pathname_prefix=routes_pathname_prefix
    )
    dash_app.title = title
    dash_app.init_app(server)
    return dash_app

def get_flask_app():
    """Delayed flask_app import"""
    from webapp.app import flask_app
    return flask_app