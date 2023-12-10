from webapp import application

import dash
import dash_bootstrap_components as dbc
from dash import dcc
from dash import html
from dash.dependencies import Input, Output, State
from dash import dash_table
from dash import no_update
from flask import Flask, session
import pandas as pd
import numpy as np

import plotly.graph_objects as go
import plotly.express as px

# Global variable to store the investments
investments = []
portfolioSettings = {
    'Start Investment Amount': 1000,
    'Monthly Investment': 100,
    'Investment Time (years)': 4
}

from webapp import application


# Initialize Dash app with the existing Flask server
dash_app = dash.Dash(__name__, server=application, external_stylesheets=[dbc.themes.BOOTSTRAP], routes_pathname_prefix='/dash/portfolioProjection/')
server = dash_app.server

TOOLTIP_STYLE = {"background-color": "black", "color": "white", "border-radius": "5px"}
LABEL_STYLE = {'font-weight': 'bold'}
H6_STYLE = {'textAlign': 'center', 'padding': '5px', 'fontWeight': 'bold', 'fontStyle': 'italic'}

MAX_INVESTMENT_TIME = 40

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

# --------------------- CALLBACKS SECTION --------------

def calc_portfolio(portfolioSettings):

    global investments

    if 'investments' in session and session['investments']:
        investments = session['investments']
        df = pd.DataFrame(investments)
    else:
        return no_update
    
    startInvestment = portfolioSettings.get('Start Investment Amount', 0)
    monthlyInvestment = portfolioSettings.get('Monthly Investment', 0)
    investmentTime = portfolioSettings.get('Investment Time (years)', 0)

    distinctInvestments_amount = df.shape[0]
    # re-scaling idealProportion and expectedGrowth
    df['ideal_proportion'] /= df['ideal_proportion'].sum()
    df['expected_growth'] /= 100

    # Re-labeling risks and volatility
    df['investment_strategy'] = df['investment_strategy'].map({
                                                                'Conservative': 1.0375,
                                                                'Medium': 1.075,
                                                                'Risky': 1.15
                                                            })

    df['asset_volatility'] = df['asset_volatility'].map({
                                                        'High': 10,
                                                        'Mid': 6,
                                                        'Low': 3
                                                    })
    
    # Disabling random number generation where necessary
    df.loc[df['random_growth'] == False, 'asset_volatility'] = 0

    # Basically a linear function, with sine-wave at the higher end to smooth it.
    thresholdProportion = \
        np.minimum(
            (np.sin(df['ideal_proportion'] * 0.5 * np.pi)
                + (df['ideal_proportion'] * 0.7))/ (0.7 + 1),
            df['ideal_proportion'] * df['investment_strategy']
    )

    investmentTime_inWeeks = investmentTime * 52
    
    # Initializing balances and setting actual investment amount for each investment
    totalSold = np.zeros(distinctInvestments_amount)
    totalBought = np.zeros(distinctInvestments_amount)
    currentAmount = np.array(startInvestment * df['ideal_proportion'])

    # Initializing random_values
    random_values = None

    # (if enabled) Pre-calculate Expected Growth decay
    # Tends to the median growth (if growth > median)
    median_growth = df['expected_growth'].median()

    # Compound interest conversion from annual to weekly growth
    df['expected_growth'] = (1 + df['expected_growth']) ** (1/52) - 1

    decay_2DList = np.array([
        np.linspace(
            start,
            ((median_growth * 10 + start) / 11),
            num=investmentTime_inWeeks
        ) if start > median_growth else np.full(investmentTime_inWeeks, start)
        for start in df['expected_growth']
    ])

    # ------------ Pre calculating random values section
    def vectorized_genPseudoRdNum(
            weeks,randomStd, nameLen,
            vol_Dur,vol_Mag, volPhase,
            trend_Dur, trend_Mag, trendPhase
            ):
        
        '''
            Generates an ndArray of 'weeks' size with pre-calculations for bull-bear cycles, and volatility cycles.
            This function is divided in x steps:
                - It calculates a predictable seed
                - Transforms user input into formula-friendly versions
                - Use Sine wave functions to oscillate both cycles
                - Returns pseudo-random number for all weeks, with oscilating mean (bbCycles) and spread (volCycles)

        '''

        # This makes the seed predictable, enabling the user to test portfolio performance on average if he wants to.
        nameLen_ext = np.tile(nameLen, (len(weeks), 1)) # making nameLen match the shape of weeks
        seedCalc = ((weeks + nameLen_ext[:,0])).astype(int)
        np.random.seed(seedCalc)

        # Formula for translating years to the phased cycle 
        transformed_vol_Dur = (1/vol_Dur/52)
        transformed_trend_Dur = (1/trend_Dur/52)

        # Allows the user to pick the phase of each cycle
        vol_phaseShift = volPhase * np.pi / (transformed_trend_Dur * np.pi)
        bb_phaseShift = trendPhase * (2 * np.pi) / (transformed_trend_Dur * np.pi)
        
        volatilityCycle = np.maximum(
                            np.abs(
                                np.sin(
                                    (weeks[:, np.newaxis] - vol_phaseShift) * transformed_vol_Dur * np.pi
                                ) * vol_Mag
                            ) + 1e-10,
                        0.35) # Minimum Volatility allowed

        # ---------------- Making Volatility Cycles have a floor. Floor is smoothed for niceness
        def sigmoid(x):
            return 1 / (1 + np.exp(-x))

        PARAM_FLOOR = 0.5
        scaling_factor = 1 / PARAM_FLOOR * 1.4 # empirically gives the smoothest curves for any PARAM_FLOOR
        scaled_volatility = (volatilityCycle - PARAM_FLOOR) * scaling_factor

        sVolatilityCycle = sigmoid(scaled_volatility) * (volatilityCycle - PARAM_FLOOR) + PARAM_FLOOR

        # wrapping trend's formula in a function allows me to easily cap de-growth
        def trendCycle_func(weeks, transformed_trend_Dur, bb_phaseShift, trend_Mag):
            return (np.sin((weeks[:, np.newaxis] - bb_phaseShift) * transformed_trend_Dur * np.pi) * trend_Mag)
        
        trendCycle = np.maximum(trendCycle_func(weeks, transformed_trend_Dur, bb_phaseShift, trend_Mag),
                        trendCycle_func(weeks, transformed_trend_Dur, bb_phaseShift, trend_Mag = np.minimum(0.95, trend_Mag)))


        # Create an array of random numbers with shape (investmentTime_inWeeks, number_of_rows)
        return np.array([np.random.normal(1 * (1+trendCycle[i]), randomStd * sVolatilityCycle[i]) 
                                for i in range(len(weeks))])
    

    
    if df['random_growth'].any(): # skipping pre-calculation if there's no randomGrowth checked
        weeks = np.arange(1, investmentTime_inWeeks + 1)
        random_values = vectorized_genPseudoRdNum(
            weeks, 
            df['asset_volatility'].to_numpy(), 
            df['investment_id'].str.len().to_numpy(),
            df['volatility_duration'].to_numpy(),
            df['volatility_magnitude'].to_numpy(),
            df['volatility_phase'].to_numpy(),
            df['bullbear_duration'].to_numpy(),
            df['bullbear_magnitude'].to_numpy(),
            df['bullbear_phase'].to_numpy()
        )

    results = []
    for week in range(1, investmentTime_inWeeks + 1):
        # Getting precalculated values for Decay Growth
        weekGrowth = decay_2DList[:, week-1]        
        
        # skipping calculation if there's no randomGrowth checked
        if random_values is not None:
            weekGrowth *=  random_values[week - 1]

        # Casting compound growth
        currentAmount += currentAmount * weekGrowth

        # -------------------- Rebalancing Portfolio Section
        thresholdInvestment = thresholdProportion * currentAmount.sum()
        idealInvestment = df['ideal_proportion'] * currentAmount.sum()

        # Calculate the Selling Delta based on threshold trigger
        sellingDelta = np.maximum(currentAmount - thresholdInvestment, np.zeros(distinctInvestments_amount))        

        totalSold += sellingDelta

        # Update the 'Current Amount' column based on threshold trigger
        currentAmount = np.minimum(currentAmount, thresholdInvestment)
        soldAmount = sellingDelta.sum()

        # Calculate toBuy delta (how much each investment needs to be bought in theory)
        toBuy_Delta = np.maximum(idealInvestment - currentAmount, np.zeros(distinctInvestments_amount))

        # Actually 'buying' assets, with the money left in 'soldAmount' + Monthly Contributions
        #  First half: transform toBuy_Delta in proportion
        # Second half: multiply each proportion with the amount of money in the balance
        toBuy_Proportion = toBuy_Delta / (toBuy_Delta.sum() + 1e-10)

        if np.sum(toBuy_Proportion) == 0:
            toBuy_Proportion = np.full(distinctInvestments_amount, 1/distinctInvestments_amount)

        boughtValues =  toBuy_Proportion * np.round(soldAmount + (monthlyInvestment*12/52), 2)

        totalBought += boughtValues

        currentAmount += boughtValues
        actualProportion = currentAmount / (currentAmount.sum() + 1e-10)
        # --------------------------- Storing Info in TimeLine

        results.extend(list(zip(df['investment_id'], currentAmount, [week]*distinctInvestments_amount, totalSold, totalBought, actualProportion)))


    return pd.DataFrame(
                        results,
                        columns=[
                            'investment_id','Current Amount ($)','Week',
                            'Total Sold','Total Bought','Actual Proportion (%)'
                        ])

# Callback for disabling options when random-growth-check is off
@dash_app.callback(
    [
        Output('asset-volatility', 'disabled'),
        Output('advanced-settings-div', 'style')
    ],
    [Input('random-growth-check', 'value')]
)
def update_asset_volatility_and_advanced_settings(random_growth_value):
    is_disabled = len(random_growth_value) == 0
    # If checkbox is unchecked (i.e., value is empty), hide the div
    div_style = {'display': 'none'} if is_disabled else {'background': '#f5f5f5', 'padding': '2px 15px 15px 15px', 'borderRadius': '5px'}
    
    return is_disabled, div_style


# Callback for plotting the calculation
@dash_app.callback(
    Output('charts-div', 'children'),
    Input('calculate-button', 'n_clicks'),
    [
        State('investment-start-amount', 'value'),
        State('investment-monthly-amount', 'value'),
        State('investment-time-slider', 'value')
    ]      
)
def calc_and_display_portfolio(n, investment_start_amount, investment_monthly_amount, investment_time):
    global investments

    # Updating the global portfolioSettings before calling calc_portfolio
    portfolioSettings['Investment Time (years)'] = min(investment_time, MAX_INVESTMENT_TIME) # Just in case the front-end sends a huge value, cap at 40 years
    portfolioSettings['Start Investment Amount'] = investment_start_amount 
    portfolioSettings['Monthly Investment'] = investment_monthly_amount

    # df = pd.DataFrame(investments)
    timeline_df = calc_portfolio(portfolioSettings)

    # Return early if there's no update
    if timeline_df is no_update:
        return ""


    # ------------------------------- calculations for plotting -------------------------------
    # Calculate the current worth of the portfolio
    current_worth = timeline_df[timeline_df['Week'] == timeline_df['Week'].max()]['Current Amount ($)'].sum()
    investment_start_amount = 1 if investment_start_amount == 0 else investment_start_amount
    
    # Calculate the percentage growth compared to 'Start Investment Amount'
    percentage_growth = ((current_worth - investment_start_amount) / investment_start_amount + 1e-16) * 100

    # Converting Weeks to Years
    timeline_df['Current Year'] = timeline_df['Week'] // 52

    # ------------------------------- Plotting -------------------------------

    # Summary Info
    summary_div = html.Div([
        html.H3(f"Your portfolio is now worth: ${current_worth:,.2f}", style={'color': 'green', 'font-weight': 'bold'}),
        html.H5(f"Your portfolio grew by: {percentage_growth:.2f}%")
    ], style={'border': '1px solid #ddd', 'padding': '10px', 'border-radius': '5px', 'margin-bottom': '20px'})

    # Create the Pie Chart
    grouped_df = timeline_df.groupby('investment_id').sum()['Actual Proportion (%)'].reset_index()
    pie_chart = dcc.Graph(
        figure=px.pie(
            grouped_df,
            names='investment_id',
            values='Actual Proportion (%)',
            title="Investments Distribution"
            )
    )

    # Create the Line Chart for each Investment ID
    line_chart_by_type = dcc.Graph(
        figure=px.line(
            timeline_df,
            x='Week',
            y='Current Amount ($)',
            color='investment_id',
            title="Current Amount ($) through Time by Investment ID",
            hover_data=['Current Year']
            )
    )

    # Create the Line Chart for the Total Amount
    priceHistory = timeline_df.groupby('Week', as_index=False)['Current Amount ($)'].sum()
    priceHistory['Current Year'] = priceHistory['Week'] // 52
    line_chart_total = dcc.Graph(
        figure=px.line(
            priceHistory,
            x='Week',
            y='Current Amount ($)',
            title="Total Amount ($) through Time",
            hover_data= ['Current Year']
            )
    )

    # Mini table with total sold and bought amounts for each asset
    mini_table_data = timeline_df[['investment_id', 'Total Sold', 'Total Bought']].groupby('investment_id', as_index = False).sum().round(2)
    mini_table = dash_table.DataTable(
        id='mini-investment-table',
        columns=[{'name': i, 'id': i} for i in mini_table_data.columns],
        data=mini_table_data.to_dict('records'),
        style_table={'margin-top': '20px'}
    )

    return [
        summary_div,        
        # Row for the charts
        dbc.Row([
            dbc.Col([
                mini_table
            ], width=6, align="center"),
            
            dbc.Col([
                pie_chart
            ], width=6)
        ]),
        line_chart_by_type, 
        line_chart_total
    ]

if __name__ == '__main__':
    #investments = []  # Reset the investments list on server restart or page refresh
    application.run(debug=True)