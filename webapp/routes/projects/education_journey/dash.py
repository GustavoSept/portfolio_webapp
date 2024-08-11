import os
import sqlite3
from dash import Dash, dcc, html

import pandas as pd
import dash_bootstrap_components as dbc

from .callbacks import DashCallbacks
from webapp.helpers.db import should_fetch_df, save_df_to_sqlite

def fetch_and_process_data() -> pd.DataFrame:
    url = 'https://docs.google.com/spreadsheets/d/17_Eq4kJ6LE4hVF-kaa6P6YOy07bukCtQuMHYcNYLjWc/export?format=csv'
    df = pd.read_csv(url)
    df = df[df['Specific Content'].notna()] # deleting rows with NaN values
    df = preprocess_labels(df, 'Label')
    save_df_to_sqlite(df)
    return df

def get_data_from_sqlite() -> pd.DataFrame:
    BASE_DIR = os.getenv('DB_BASE_DIR')
    db_path = os.path.join(BASE_DIR, 'education_journey.db')
    with sqlite3.connect(db_path) as conn:
        df = pd.read_sql_query("SELECT * FROM education_journey", conn)
    return df

def preprocess_labels(df: pd.DataFrame, column_name: str) -> pd.DataFrame:
    """Preprocesses the labels in the specified column by appending numeric suffixes to duplicate labels"""
    label_counts = df[column_name].value_counts()
    for label, count in label_counts.items():
        if count > 1:
            label_rows = df[df[column_name] == label]
            new_labels = [f"{i+1}_{label}" for i in range(count)]
            df.loc[label_rows.index, column_name] = new_labels
    return df

def dash_educational_journey(flask_app):
    dash_app = Dash(
            __name__,
            server=flask_app,
            external_stylesheets=[dbc.themes.BOOTSTRAP],
            routes_pathname_prefix="/dash/educationJourney/",
            suppress_callback_exceptions=True,
            )


    if should_fetch_df():
        df = fetch_and_process_data()
    else:
        df = get_data_from_sqlite()

    HOURS_STUDIED = int(df['Time (in hours)'].sum())
    UNIQUE_INSTITUTIONS = df['Institution'].unique()

    # checklist to filter data between institutions
    checklist = dcc.Checklist(
        id='institution-checklist',
        options=[{'label': i, 'value': i} for i in UNIQUE_INSTITUTIONS],
        value=list(UNIQUE_INSTITUTIONS),  # Initially, all options are selected
        inline=False
    )

    toggle_button = dbc.Button(
        "Filter by Institutions",
        id='toggle-button',
        n_clicks=0,
        color="primary",  # Bootstrap color style
        className="me-1",  # Bootstrap spacing class (margin end)
        style={'width': 'auto', 'height': 'auto'}
    )


    checklist_div = html.Div(
        id='checklist-div',
        children=[
            html.Div([checklist], style={'text-align': 'left', 'margin-left': '35%'})
        ],
        style={'display': 'none'}  # Keeping the initially hidden property
    )


    dash_app.layout = html.Div([
        dbc.Row([
            html.H1("My Personal Learning Journey"),
            dbc.Col([  # Column 1 with responsive width
                html.H3([
                    "Studied for ",
                    html.Span(f"{HOURS_STUDIED} hours", style={'color': '#0077b6', 'font-weight': 'bold', 'font-size': 'larger'}),
                    " in total."
                ]),
                html.P([
                    "Check my ",
                    html.A("Notion Wiki", href="https://gustavosept.notion.site/gustavosept/Studies-d197367eb0284ebeb86ed1ae194d45d6", style={'font-weight': 'bold'}, target="_blank"),
                    " for in-depth material."
                ], style={'margin-top': '10px'})
            ], lg=6, md=12),  # Larger screens get a half width, smaller screens full width
            dbc.Col([  # Column 2 with responsive width
                html.Div([
                    toggle_button,
                    checklist_div,
                    html.Div([
                        html.Label('Click chart to filter groups'),
                        html.Br(),
                        html.Label('and access source material.'),
                    ], style={
                        'font-style': 'italic',
                        'color': 'grey',
                        'font-size': 'smaller'
                    })
                ], style={'text-align': 'right'})
            ], lg=6, md=12)  # Same as above
        ]),
        dbc.Row([
            dbc.Col([
                dcc.Graph(id='sunburst-chart', style={'width': '100%', 'height': '80vh'})
            ])
        ]),
        dcc.Store(id='store-url'),
        html.Div(id='hidden-div', style={'display': 'none'}, children='init'),
        html.Div(id='dummy-div', style={'display': 'none'})
    ], style={'max-width': '100vw', 'overflow-x': 'hidden'})

    DashCallbacks(dash_app, df)

