from flask import Flask
import logging

application = Flask(__name__, static_url_path='/static')
application.secret_key = 'your_secret_key'
application.logger.setLevel(logging.INFO)


# needs to come after app instance is created
from webapp import routes
from webapp import portfolioProjection
from webapp import compoundInterest
from webapp import data_fetcher
from webapp import educationJourney

# for rule in application.url_map.iter_rules():
#     print(rule)
