from webapp import application
from flask import render_template
import requests

@application.route('/')
def pg_home():    
    return render_template('home.html')
