from dash import Dash, dcc, html, Output, Input, State, no_update

import logging
import pandas as pd
import plotly.express as px
import dash_bootstrap_components as dbc


class DashCallbacks:
    
    def __init__(
        self,
        dash_app,
        df,
    ) -> None:
        self.dash_app: Dash = dash_app
        self.df: pd.DataFrame = df
        self.register_callbacks()
    
    
    def register_callbacks(self):
        @self.dash_app.callback(
            Output('sunburst-chart', 'figure'),
            [Input('institution-checklist', 'value')]  # Input from the checklist
        )
        def update_chart(selected_institutions):
            """Function and callback to plot the chart (and filter it)"""
            logging.info("update_chart(selected_institutions) was just called...")
            # Filter the DataFrame based on selected institutions
            filtered_df = self.df[self.df['Institution'].isin(selected_institutions)]
            
            # Create and return the updated sunburst chart
            return self.create_sunburst(filtered_df)


        @self.dash_app.callback(
            Output('store-url', 'data'),  # Update the store instead of the URL directly
            [Input('sunburst-chart', 'clickData')]
        )
        def store_url(clickData):
            """Function and callback to make the sunburst plot clickable for links"""
            if clickData:
                # Extracting the clicked part
                custom_data = clickData['points'][0]['customdata']
                url = custom_data[1]  # 'Source Link' is the second element in custom_data

                if url.startswith('http'):
                    return {'url': url}
            return no_update

        # Clientside callback to open a new window
        self.dash_app.clientside_callback(
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
        @self.dash_app.callback(
            Output('checklist-div', 'style'),
            [Input('toggle-button', 'n_clicks')],
            [State('checklist-div', 'style')]
        )
        def toggle_checklist_visibility(n_clicks, style):
            if n_clicks % 2 == 0:  # Toggle visibility on each click
                return {'display': 'none'}
            else:
                return {'display': 'block'}


        @self.dash_app.callback(
            Output('dropdown-state', 'data'),
            [Input('dropdown-label', 'n_clicks')],
            [State('dropdown-state', 'data')]
        )
        def toggle_dropdown_state(n_clicks, data):
            if n_clicks:
                data['expanded'] = not data['expanded']
            return data

    def create_sunburst(self, df: pd.DataFrame):
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
