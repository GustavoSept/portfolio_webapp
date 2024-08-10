from webapp.app import flask_app


def main():    
    flask_app.run(
        debug=True,
        host='webapp',
        port=8000,
        load_dotenv=True,
    )


if __name__ == '__main__':
    main()