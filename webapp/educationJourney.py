from webapp import application

from flask import Flask
from dash import dcc, html, Dash, Output, Input, no_update

import json
import pandas as pd
import plotly.express as px

# Load data from the Google Sheets URL
url = 'https://docs.google.com/spreadsheets/d/17_Eq4kJ6LE4hVF-kaa6P6YOy07bukCtQuMHYcNYLjWc/export?format=csv'
df = pd.read_csv(url)

# deleting rows with NaN values
df = df[df['Specific Content'].notna()]

# Preprocessing the 'Label' column, to mantain divisions
def preprocess_labels(df, column_name):
    label_counts = df[column_name].value_counts()
    
    # For labels that occur more than once, add a prefix
    for label, count in label_counts.items():
        if count > 1:
            # Filter rows with the current label
            label_rows = df[df[column_name] == label]
            
            # Generate new labels with prefixes
            new_labels = [f"{i+1}_{label}" for i in range(count)]
            
            df.loc[label_rows.index, column_name] = new_labels

    return df

df = preprocess_labels(df, 'Label')

def create_sunburst(df):
    fig = px.sunburst(
        df,
        path=['Group', 'SubGroup', 'Label'],  # Define the hierarchy
        values='Time (in hours)',
        color='Group',
        custom_data=['Specific Content', 'Source Link']
    )

    fig.update_traces(
        insidetextorientation='radial',

        # Customizing the tooltip
        hovertemplate=\
            "<b>%{label}</b><br>Specific Content: %{customdata[0]}<br>Time: %{value}h<extra></extra>",  
    )
    fig.update_layout(
        width= 1200,
        height=1200
    )

    return fig

# Create your Dash app
app = Dash(__name__, server=application, url_base_pathname='/dash/educationJourney/')

app.layout = html.Div([
    html.H1("My Personal Learning Journey"),
    dcc.Graph(id='sunburst-chart'),
    dcc.Store(id='store-url'),  # Store component to hold the URL
    html.Div(id='hidden-div', style={'display': 'none'}, children='init'),  # Hidden div
    html.Div(id='dummy-div', style={'display': 'none'})  # Dummy div for clientside callback
])

@app.callback(
    Output('sunburst-chart', 'figure'),
    [Input('hidden-div', 'children')]  # Hidden div as a trigger to show chart
)
def update_chart(trigger):    
    fig = create_sunburst(df)
    return fig


# This callback and function makes the sunburst plot clickable for links
@app.callback(
    Output('store-url', 'data'),  # Update the store instead of the URL directly
    [Input('sunburst-chart', 'clickData')]
)
def store_url(clickData):
    if clickData:
        # Extracting the clicked part
        custom_data = clickData['points'][0]['customdata']
        url = custom_data[1]  # 'Source Link' is the second element in custom_data
        return {'url': url}
    return no_update

# Clientside callback to open a new window
app.clientside_callback(
    """
    function(data) {
        if(data && data.url) {
            window.open(data.url, '_blank');
        }
    }
    """,
    Output('dummy-div', 'children'),  # Dummy output, not used
    [Input('store-url', 'data')]
)

if __name__ == '__main__':
    application.run_server(debug=True)

