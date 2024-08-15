import logging
from webapp.app import flask_app


def main():
    logging.basicConfig(level=10)    
    flask_app.run(
        debug=True,
        host='webapp',
        port=8000,
        load_dotenv=True,
    )


if __name__ == '__main__':
    main()