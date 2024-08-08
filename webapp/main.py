import os
import logging

from flask import Flask
from dotenv import load_dotenv

from webapp.routes import main_bp

def main():

    load_dotenv()

    application = Flask(__name__, static_url_path='/static')
    application.secret_key = os.getenv('FLASK_SECRET')
    application.logger.setLevel(logging.INFO)
    
    application.register_blueprint(main_bp)
    
    for rule in application.url_map.iter_rules():
        print("application.url_map.iter_rules()")
        print(f"{rule = }")
        
    application.run(debug=True, host='0.0.0.0', port=8000)


if __name__ == '__main__':
    main()
