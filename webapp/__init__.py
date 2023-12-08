from flask import Flask

application = Flask(__name__)

# needs to come after app instance is created
from webapp import routes