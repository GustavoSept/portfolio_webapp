import logging
from flask import Flask
from dotenv import load_dotenv

from webapp.routes import main_bp, import_routes
from webapp.routes.projects.portfolio_projection.dash import dash_portfolio_projection


load_dotenv()

def make_flask_app():
    flask_app = Flask(
        __name__,
        template_folder='./templates',
        static_folder='./static',
    )
    flask_app.logger.setLevel(logging.INFO)

    flask_app.config.from_prefixed_env()

    import_routes()

    flask_app.register_blueprint(main_bp)

    dash_portfolio_projection(flask_app)

    for rule in flask_app.url_map.iter_rules():
        print(f"Endpoint: {rule.endpoint}\n Route: {rule.rule}\n Methods: {rule.methods}\n\n")
    
    return flask_app


flask_app = make_flask_app()