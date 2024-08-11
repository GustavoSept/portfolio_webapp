from dash import Dash, dcc, html
import dash_bootstrap_components as dbc

from .callbacks import DashCallbacks
from ..portfolio_projection import (
    H6_STYLE, LABEL_STYLE, MAX_INVESTMENT_TIME,
)

def dash_portfolio_projection(flask_app):
    dash_app = Dash(
            __name__,
            server=flask_app,
            external_stylesheets=[dbc.themes.BOOTSTRAP],
            routes_pathname_prefix="/dash/portfolioProjection/",
            suppress_callback_exceptions=True,
        )

    dash_app.layout = dbc.Container([
        dbc.Row(
            dbc.Col([

                html.H1('Portfolio Value Projection', style={'textAlign': 'center', 'padding': '20px'}),

                # Portfolio Settings
                html.Div([
                    html.H6('Portfolio Settings', style={**H6_STYLE, 'color': '#55bee0'}),
                    dbc.Row([
                        dbc.Col([
                            html.Label('Investment Starting Point', style=LABEL_STYLE),
                            dcc.Input(id='investment-start-amount', type='number', placeholder='Enter Investment Amount', value=1000, style={'width': '100%'})
                        ], width=6, align="center"),
                        
                        dbc.Col([
                            html.Label('Monthly Investment', style=LABEL_STYLE),
                            dcc.Input(id='investment-monthly-amount', type='number', placeholder='Enter Investment Amount', value=100, style={'width': '100%'})
                        ], width=6, align="center")
                    ]),
                    
                    html.Label('Investment Time (years)', style=LABEL_STYLE),
                    dcc.Slider(id='investment-time-slider', min=0, max=MAX_INVESTMENT_TIME, step=1, value=4,
                            marks={i: str(i) for i in range(0, MAX_INVESTMENT_TIME+1, 1)})
                ], style={'background': '#f5f5f5', 'padding': '2px 15px 15px 15px', 'borderRadius': '5px'}),

                html.Br(),

                # Action Buttons
                html.Div([
                    html.Button('Calculate Portfolio', id='calculate-button', className='btn btn-primary', style={'marginRight': '10px'})
                ]),

                # Error Message Area
                html.Div(id='error-message-div', style={'color': 'red', 'marginTop': '10px'}),

                # Hidden Containers
                html.Div(id='div-assetsBackup', style={'display': 'none'}),
                html.Div(id='hide-table-flag', style={'display': 'none'}),

                # Display Areas
                dcc.Loading(
                    id="loading-external",
                    type="default",
                    children=[
                        html.Div(id='charts-div', style={'height': '100%'})
                    ],
                    style={'height': '100%', 'display': 'flex', 'alignItems': 'flex-start'}
                ),
            ])
        )  
    ], fluid=True, style={'marginTop': '20px'})

    DashCallbacks(dash_app)