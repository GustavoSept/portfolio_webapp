import logging
import os
from webapp.app import flask_app

WEBAPP_IP = os.getenv("WEBAPP_IP")
WEBAPP_PORT = os.getenv("WEBAPP_PORT")

def main():
    logging.basicConfig(level=10)    
    flask_app.run(
        debug=True,
        host=WEBAPP_IP,
        port=WEBAPP_PORT,
        load_dotenv=True,
    )


if __name__ == '__main__':
    main()