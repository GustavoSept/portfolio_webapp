import pandas as pd
import numpy as np
import plotly.graph_objects as go
from dash import Dash, dcc, html, Input, Output
import dash_bootstrap_components as dbc
import sqlite3
import os
from webapp.helpers.db import should_fetch_df, save_df_to_sqlite, get_data_from_sqlite

# Helper function to assign colors based on Group and Level
def assign_color(row):
    group_colors = {
        'Software Eng & CS': (0, 0, 255),  # Blue
        'Data Eng & Science': (128, 0, 128),  # Purple
        'Math': (255, 255, 0),  # Yellow
        'Management & Self-Mastery': (64, 224, 208)  # Turquoise
    }
    level_shades = {
        'Introductory': 0.3,
        'Fundamentals': 0.6,
        'Applied': 0.9
    }
    base_color = group_colors[row['Group']]
    shade = level_shades[row['Level']]
    return f"rgb({int(base_color[0]*shade)}, {int(base_color[1]*shade)}, {int(base_color[2]*shade)})"

# TODO: generate the actual logic to cluster these
# To be efficient, we should only embed each row once, and calculate clusters on every update
def preprocess_data(df: pd.DataFrame) -> pd.DataFrame:
    """Calculate clusters in the data"""
    # Assign cluster based on Group
    df['cluster'] = df['Group'].astype('category').cat.codes
    
    # Generate random positions within each cluster
    df['x'] = df.apply(lambda row: np.random.normal(row['cluster'] * 5, 1), axis=1)
    df['y'] = df.apply(lambda row: np.random.normal(row['cluster'] * 5, 1), axis=1)
    
    # Assign colors
    df['color'] = df.apply(assign_color, axis=1)
    
    return df

def create_cluster_plot(df):
    fig = go.Figure()

    for group in df['Group'].unique():
        group_data = df[df['Group'] == group]
        
        fig.add_trace(go.Scatter(
            x=group_data['x'],
            y=group_data['y'],
            mode='markers',
            marker=dict(
                size=group_data['Time (in hours)'],
                sizemode='area',
                sizeref=2.*max(df['Time (in hours)'])/(40.**2),
                sizemin=4,
                color=group_data['color']
            ),
            text=group_data.apply(
                lambda row: f"<b>{row['Specific Content']}</b><br>{row['Group']}//{row['SubGroup']}<br>"
                            f"Institution: {row['Institution']}<br>Time: {row['Time (in hours)']} hours<br>"
                            f"Language: {row['Language']}<br>Level: {row['Level']}",
                axis=1
            ),
            hoverinfo='text',
            name=group,
            customdata=group_data['Source Link']
        ))

    fig.update_layout(
        title="",
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        showlegend=True,
        hovermode='closest'
    )

    return fig

def fetch_and_process_data() -> pd.DataFrame:
    url = 'https://docs.google.com/spreadsheets/d/17_Eq4kJ6LE4hVF-kaa6P6YOy07bukCtQuMHYcNYLjWc/export?format=csv'
    df = pd.read_csv(url)
    
    # Crop the DataFrame to the last valid row based on 'Label' column
    last_valid_index = df['Label'].last_valid_index()
    df = df.loc[:last_valid_index].reset_index(drop=True)
    
    # Fill NaN values in 'Group' column with a placeholder
    df['Group'] = df['Group'].fillna('Uncategorized')
    
    df = preprocess_data(df)
    save_df_to_sqlite(df)
    return df



def dash_educational_journey(flask_app):
    dash_app = Dash(
        __name__,
        server=flask_app,
        external_stylesheets=[dbc.themes.BOOTSTRAP],
        routes_pathname_prefix="/dash/educationJourney/",
        suppress_callback_exceptions=True,
    )

    # Load and preprocess data
    if should_fetch_df():
        df = fetch_and_process_data()
    else:
        df = preprocess_data(get_data_from_sqlite(database='education_journey.db', table_name='education_journey'))

    # Add error handling for empty DataFrame
    if df.empty:
        dash_app.layout = html.Div([
            html.H1("Error: No data available"),
            html.P("Please check the data source and try again.")
        ])
    else:
        dash_app.layout = html.Div([
            dcc.Graph(id='cluster-plot', figure=create_cluster_plot(df), style={'height': '90vh'}),
            html.Div(id='dummy-output', style={'display': 'none'}),
            dcc.Location(id='url', refresh=False)
        ])


        # makes each dot clickable
        dash_app.clientside_callback(
            """
            function(clickData) {
                if (clickData && clickData.points && clickData.points.length > 0) {
                    var url = clickData.points[0].customdata;
                    window.open(url, '_blank');
                }
                return null;
            }
            """,
            Output('dummy-output', 'children'),
            Input('cluster-plot', 'clickData')
        )

    return dash_app