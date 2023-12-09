from webapp import application
from flask import render_template
import requests

@application.route('/')
@application.route('/home')
def pg_home():    
    return render_template('home.html')

@application.route('/projects/economic_freedom_analysis')
def pg_EF_Analysis():
    return render_template('projects_economicFreedomAnalysis.html')

@application.route('/projects/portfolioProjection')
def pg_portfolioProjection():
    return render_template('projects_portfolioProjection.html')

