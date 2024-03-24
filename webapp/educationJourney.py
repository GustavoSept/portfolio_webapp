from webapp import application

from dash import dcc, html, Dash, Output, Input, State, no_update
from webapp.data_fetcher import data_store

import logging
import pandas as pd
import plotly.express as px
import dash_bootstrap_components as dbc


def create_sunburst(df):
    #df = data_store['DATA_CACHE'] # It seems we never need to call this one

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
# it's dynamically updated using update_checklist_options(n) function and callback
checklist = dcc.Checklist(
    id='institution-checklist',
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
                html.Span(f"{data_store['HOURS_STUDIED']} hours", id="hours-studied", style={'color': '#0077b6', 'font-weight': 'bold', 'font-size': 'larger'}),
                " in total."
            ]),
            dcc.Interval(
                id='interval-component',
                interval=6*60*60*1000,  # in milliseconds
                n_intervals=0
            ),
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
    df = data_store['DATA_CACHE']
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

# Function and callback to update the filter categories. It's using the same interval from update_hours_studied() function
@app.callback(
    Output('institution-checklist', 'options'),
    Output('institution-checklist', 'value'),
    [Input('interval-component', 'n_intervals')]
)
def update_checklist_options(n):
    options = [{'label': i, 'value': i} for i in data_store['UNIQUE_INSTITUTIONS']]
    value = list(data_store['UNIQUE_INSTITUTIONS'])
    return options, value

# Function and callback to update HOURS_STUDIED from inside Dash's dbc component
@app.callback(
    Output('hours-studied', 'children'),
    [Input('interval-component', 'n_intervals')]
)
def update_hours_studied(n):
    return f"{data_store['HOURS_STUDIED']} hours"


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
    application.run(debug=False)

