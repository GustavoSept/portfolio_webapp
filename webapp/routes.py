from webapp import application
from flask import Flask, session, render_template, request, redirect
import re
import logging

@application.route('/')
@application.route('/home')
def pg_home():    
    return render_template('home.html')

@application.route('/contact')
def pg_contact():
    return render_template('contact.html')

@application.route('/projects/economic_freedom_analysis')
def pg_EF_Analysis():
    return render_template('projects_economicFreedomAnalysis.html')

@application.route('/projects/compoundCalculator')
def pg_compoundCalc():
    return render_template('projects_compoundInterestCalc.html')

@application.route('/projects/portfolioProjection')
def pg_portfolioProjection():

    # If user doesn't have this cookie, create a default table for him
    if 'investments' not in session:
        session['investments'] = [
        {"investment_id": "Debenture A", "ideal_proportion": 25, "investment_strategy": "Medium", "expected_growth": 9,
        "random_growth":False, "asset_volatility": "Low", "growth_decay":False, "volatility_duration": 3, "volatility_magnitude": 1,
        "volatility_phase": 0, "bullbear_duration": 4, "bullbear_magnitude": 1, "bullbear_phase":0},

        {"investment_id": "Debenture B", "ideal_proportion": 20, "investment_strategy": "Risky", "expected_growth": 11,
        "random_growth":False, "asset_volatility": "Low", "growth_decay":False, "volatility_duration": 3, "volatility_magnitude": 1,
        "volatility_phase": 0, "bullbear_duration": 4, "bullbear_magnitude": 1, "bullbear_phase":0},
        
        {"investment_id": "Bitcoin", "ideal_proportion": 5, "investment_strategy": "Conservative", "expected_growth": 30,
        "random_growth":True, "asset_volatility": "High", "growth_decay":True, "volatility_duration": 2, "volatility_magnitude": 1.2,
        "volatility_phase": 0.3, "bullbear_duration": 4, "bullbear_magnitude": 1.15, "bullbear_phase":0.80},
        
        {"investment_id": "Cardano", "ideal_proportion": 10, "investment_strategy": "Conservative", "expected_growth": 75,
        "random_growth":True, "asset_volatility": "High", "growth_decay":True, "volatility_duration": 2, "volatility_magnitude": 1.2,
        "volatility_phase": 0.5, "bullbear_duration": 4, "bullbear_magnitude": 1.35, "bullbear_phase":0.90},
        
        {"investment_id": "10-yr Treasury", "ideal_proportion": 25, "investment_strategy": "Risky", "expected_growth": 4.2,
        "random_growth":False, "asset_volatility": "Low", "growth_decay":False, "volatility_duration": 3, "volatility_magnitude": 1,
        "volatility_phase": 0, "bullbear_duration": 4, "bullbear_magnitude": 1, "bullbear_phase":0},
        
        {"investment_id": "SP500", "ideal_proportion": 15, "investment_strategy": "Medium", "expected_growth": 10,
        "random_growth":True, "asset_volatility": "Mid", "growth_decay":True, "volatility_duration": 3, "volatility_magnitude": 1,
        "volatility_phase": 0, "bullbear_duration": 10, "bullbear_magnitude": 1, "bullbear_phase":0.05},
        
        
    ]

    return render_template('projects_portfolioProjection.html', investments=session['investments'])

# ------------------------------------------------------------------
# If code grows, put these function(s) in a controllers.py file
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


@application.route('/add-investment', methods=['POST'])
def add_investment():
    data = request.get_json()

    # -------------------------------- Validation checks
    
    # Capitalize and check for duplication
    investment_id_upper = data['investment_id'].upper()
    if any(investment['investment_id'] == investment_id_upper for investment in session.get('investments', [])):
        return {'status': 'error', 'message': 'Duplicate investment_id'}
    
    # More restrictions for input
    if 'investment_id' not in data or not re.match("^[A-Za-z0-9_ -]+$", data['investment_id']):
        return {'status': 'error', 'message': 'Invalid investment_id'}
    data['investment_id'] = data['investment_id'].upper()

    if 'investment_strategy' not in data or data['investment_strategy'] not in ['Risky', 'Medium', 'Conservative']:
        return {'status': 'error', 'message': 'Invalid investment_strategy'}

    if 'asset_volatility' not in data or data['asset_volatility'] not in ['Low', 'Mid', 'High']:
        return {'status': 'error', 'message': 'Invalid asset_volatility'}

    boolean_fields = ['growth_decay', 'random_growth']
    for field in boolean_fields:
        if field in data:
            try:
                data[field] = bool(data[field])
            except ValueError:
                return {'status': 'error', 'message': f'Invalid value for {field}'}

    float_fields = ['ideal_proportion', 'expected_growth', 'volatility_duration', 'volatility_magnitude', 'volatility_phase', 'bullbear_duration', 'bullbear_magnitude', 'bullbear_phase']
    for field in float_fields:
        if field in data:
            try:
                data[field] = float(data[field])
            except ValueError:
                return {'status': 'error', 'message': f'Invalid value for {field}'}

    # -------------------------------- All checks passed, add to session
    if 'investments' not in session:
        session['investments'] = []

    session['investments'].append(data)
    session['investments'] = session['investments'] # Reassigning to session to force update

    return {'status': 'success'}
