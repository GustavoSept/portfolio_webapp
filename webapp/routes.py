from webapp import application
from flask import Flask, session, render_template
from flask import request
import logging

@application.route('/')
@application.route('/home')
def pg_home():    
    return render_template('home.html')

@application.route('/projects/economic_freedom_analysis')
def pg_EF_Analysis():
    return render_template('projects_economicFreedomAnalysis.html')

@application.route('/projects/portfolioProjection')
def pg_portfolioProjection():

    if 'investments' not in session:
        session['investments'] = [
        {"investment_id": "A", "ideal_proportion": 20, "investment_strategy": "Strategy A", "expected_growth": 5,
        "random_growth":True, "asset_volatility": 1, "growth_decay":True, "volatility_duration": 3, "volatility_magnitude": 1,
        "volatility_phase": 0, "bullbear_duration": 4, "bullbear_magnitude": 1, "bullbear_phase":0},
        
        {"investment_id": "B", "ideal_proportion": 50, "investment_strategy": "Strategy A", "expected_growth": 5,
        "random_growth":True, "asset_volatility": 1, "growth_decay":True, "volatility_duration": 3, "volatility_magnitude": 1,
        "volatility_phase": 0, "bullbear_duration": 4, "bullbear_magnitude": 1, "bullbear_phase":0},

        {"investment_id": "C", "ideal_proportion": 30, "investment_strategy": "Strategy A", "expected_growth": 5,
        "random_growth":False, "asset_volatility": 1, "growth_decay":True, "volatility_duration": 3, "volatility_magnitude": 1,
        "volatility_phase": 0.5, "bullbear_duration": 4, "bullbear_magnitude": 1, "bullbear_phase":0.5},
    ]

    return render_template('projects_portfolioProjection.html', investments=session['investments'])

# ------------------------------------------------------------------
# If code grows, put this/these function(s) in a controllers.py file
# ------------------------------------------------------------------


@application.route('/delete-investment', methods=['POST'])
def delete_investment():
    data = request.get_json()
    investment_id = data.get('investment_id')

    logging.debug(f"Deleting investment: {investment_id}")

    if 'investments' not in session:
        return {'status': 'error'}
    
    investmentsList = session['investments']
    investmentsList = [inv for inv in investmentsList if inv['investment_id'] != investment_id]
    session['investments'] = investmentsList  # Reassigning to session to force update

    return {'status': 'success'}
