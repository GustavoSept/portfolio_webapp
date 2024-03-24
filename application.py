from webapp import application
from webapp.data_fetcher import start_data_fetcher

if __name__ == '__main__':
    # Start the data fetcher
    start_data_fetcher()

    # Start the web application
    application.run(debug=False, host='0.0.0.0', port=5000)
