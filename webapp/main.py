from webapp.app import make_flask_app

from flask import Flask

def main():
    flask_app = make_flask_app()
    flask_app.run(
        debug=True,
        host='webapp',
        port=8000,
        load_dotenv=True,
    )


if __name__ == '__main__':
    main()