from flask import Flask

application = Flask(__name__, static_url_path='/static')
application.secret_key = 'your_secret_key'

# needs to come after app instance is created
from webapp import routes
from webapp import portfolioProjection
from webapp import compoundInterest
from webapp import educationJourney

# for rule in application.url_map.iter_rules():
#     print(rule)
