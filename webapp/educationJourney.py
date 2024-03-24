from webapp import application

from dash import dcc, html, Dash, Output, Input, State, no_update

import logging
import pandas as pd
import plotly.express as px
import dash_bootstrap_components as dbc

logging.info("start of educationJourney.py was called")

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
    # df = data_store['DATA_CACHE'] # It seems we never need to call this one

    # Pre-process your DataFrame to combine 'Theme' and 'Level' for nuanced color mapping
    df['Theme_Level'] = df.apply(lambda row: f"{row['Theme']} - {row['Level']}", axis=1)

    # Defining a nuanced and attractive color map
    color_map = {
        '(?)': '#e0e1dd',
        
        # Base colors for themes [they seem to not do much, yet i'll keep them here]
        'Data Eng & Science': '#91bdcc',
        'Software Eng & CS': '#f58c8d',
        'Math': '#faa307',
        'Management & Self-Mastery': '#a3b18a',

        # Blues
        'Data Eng & Science - Introductory': '#91bdcc',
        'Data Eng & Science - Fundamentals': '#60a6bd',
        'Data Eng & Science - Applied': '#0c7294',

        # Reds
        'Software Eng & CS - Introductory': '#f58c8d',
        'Software Eng & CS - Fundamentals': '#de3c3f',
        'Software Eng & CS - Applied': '#ba181b',

        # Yellows
        'Math - Introductory': '#faa307',
        'Math - Fundamentals': '#f48c06',  
        'Math - Applied': '#e85d04',

        # Green
        'Management & Self-Mastery - Introductory': '#bff2d2',
        'Management & Self-Mastery - Fundamentals': '#80d9a1',  
        'Management & Self-Mastery - Applied': '#65c287',
    }

    fig = px.sunburst(
        df,
        path=['Theme', 'Level', 'SubGroup', 'Content Type', 'Label'],  # Define the hierarchy
        values='Time (in hours)',
        color='Theme_Level',
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
    children=[
        html.Div([checklist], style={'text-align': 'left', 'margin-left': '35%'})
    ],
    style={'display': 'none'}  # Keeping the initially hidden property
)


app.layout = html.Div([
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




# Function and callback to plot the chart (and filter it)
@app.callback(
    Output('sunburst-chart', 'figure'),
    [Input('institution-checklist', 'value')]  # Input from the checklist
)
def update_chart(selected_institutions):
    logging.info("update_chart(selected_institutions) was just called...")
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
    application.run(debug=True)

