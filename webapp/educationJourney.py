from webapp import application

from flask import Flask
from dash import dcc, html, Dash, Output, Input
import pandas as pd
import plotly.express as px

# Load data from the Google Sheets URL
url = 'https://docs.google.com/spreadsheets/d/17_Eq4kJ6LE4hVF-kaa6P6YOy07bukCtQuMHYcNYLjWc/export?format=csv'
df = pd.read_csv(url)

# deleting rows with NaN values
df = df[df['Specific Content'].notna()]

def create_sunburst(df):
    fig = px.sunburst(
        df,
        path=['Group', 'SubGroup', 'Specific Content'],  # Define the hierarchy
        values='Time (in hours)',
        color='Group',
        title="Personal Learning Journey",
    )
    return fig

# Create your Dash app
app = Dash(__name__, server=application, url_base_pathname='/dash/educationJourney/')

app.layout = html.Div([
    html.H1("My Personal Learning Journey"),
    dcc.Graph(id='sunburst-chart'),
    html.Div(id='hidden-div', style={'display': 'none'}, children='init')  # Hidden div
])
@app.callback(
    Output('sunburst-chart', 'figure'),
    [Input('hidden-div', 'children')]  # Hidden div as a trigger to show chart
)
def update_chart(trigger):    
    fig = create_sunburst(df)
    return fig

if __name__ == '__main__':
    application.run_server(debug=True)

