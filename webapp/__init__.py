from flask import Flask

application = Flask(__name__)
application.secret_key = 'your_secret_key'

# needs to come after app instance is created
from webapp import routes
from webapp import portfolioProjection