from webapp import application

from dash import dcc, html, Dash, Output, Input, State, no_update

import pandas as pd
import plotly.express as px
import dash_bootstrap_components as dbc

# Load data from the Google Sheets URL
url = 'https://docs.google.com/spreadsheets/d/17_Eq4kJ6LE4hVF-kaa6P6YOy07bukCtQuMHYcNYLjWc/export?format=csv'
df = pd.read_csv(url)

# deleting rows with NaN values
df = df[df['Specific Content'].notna()]

HOURS_STUDIED = int(df['Time (in hours)'].sum())
UNIQUE_INSTITUTIONS = df['Institution'].unique()

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

    color_map = {
        '(?)': 'darkblue',
        'Applied Computing': '#264653',
        'Data Science': '#2a9d8f',
        'Computer Science': '#e9c46a',
        'Software and Systems Development': '#f4a261',
        'Math': '#e76f51'
    }

    fig = px.sunburst(
        df,
        path=['Group', 'SubGroup', 'Label'],  # Define the hierarchy
        values='Time (in hours)',
        color='Group',
        custom_data=['Specific Content', 'Source Link', 'Institution'],
        color_discrete_map=color_map
    )

    fig.update_traces(
        insidetextorientation='radial',

        # Customizing the tooltip
        hovertemplate=\
            "<b>%{customdata[0]}</b><br>%{label}<br>Time: %{value}h<br>Institution: %{customdata[2]}<extra></extra>",  
    )    

    return fig

# Create your Dash app
app = Dash(__name__, server=application, url_base_pathname='/dash/educationJourney/', external_stylesheets=[dbc.themes.BOOTSTRAP])

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
    children=[checklist],
    style={'display': 'none'}  # Initially hidden
)

app.layout = html.Div([
    html.H1("My Personal Learning Journey"),
    html.H3([
        "Studied for ",
        html.Span(f"{HOURS_STUDIED} hours", style={'color': '#0077b6', 'font-size': 'larger'}),
        " in total."]),
    dcc.Store(id='dropdown-state', data={'expanded': False}),  # Keep track of the dropdown state
    html.Div(
        html.Label('Click chart to filter groups, or access source material.'),
    ),
    toggle_button,  # Dropdown acting as a label
    checklist_div,   # Div containing the checklist
    dcc.Graph(id='sunburst-chart', style={'width': '100%', 'height': '80vh'}),
    dcc.Store(id='store-url'),  # Store component to hold the URL
    html.Div(id='hidden-div', style={'display': 'none'}, children='init'),  # Hidden div
    html.Div(id='dummy-div', style={'display': 'none', 'display': 'flex'})  # Dummy div for clientside callback
    ])

# Function and callback to plot the chart (and filter it)
@app.callback(
    Output('sunburst-chart', 'figure'),
    [Input('institution-checklist', 'value')]  # Input from the checklist
)
def update_chart(selected_institutions):
    # Filter the DataFrame based on selected institutions
    filtered_df = df[df['Institution'].isin(selected_institutions)]
    
    # Create and return the updated sunburst chart
    return create_sunburst(filtered_df)


# Function and callback to make the sunburst plot clickable for links
@app.callback(
    Output('store-url', 'data'),  # Update the store instead of the URL directly
    [Input('sunburst-chart', 'clickData')]
)
def store_url(clickData):
    if clickData:
        # Extracting the clicked part
        custom_data = clickData['points'][0]['customdata']
        url = custom_data[1]  # 'Source Link' is the second element in custom_data

        if url.startswith('http'):
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

# Function and callback to make the dropdown work
@app.callback(
    Output('checklist-div', 'style'),
    [Input('toggle-button', 'n_clicks')],
    [State('checklist-div', 'style')]
)
def toggle_checklist_visibility(n_clicks, style):
    if n_clicks % 2 == 0:  # Toggle visibility on each click
        return {'display': 'none'}
    else:
        return {'display': 'block'}


@app.callback(
    Output('dropdown-state', 'data'),
    [Input('dropdown-label', 'n_clicks')],
    [State('dropdown-state', 'data')]
)
def toggle_dropdown_state(n_clicks, data):
    if n_clicks:
        data['expanded'] = not data['expanded']
    return data


if __name__ == '__main__':
    application.run_server(debug=True)

