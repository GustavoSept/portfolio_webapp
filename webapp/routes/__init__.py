from flask import Blueprint

# from webapp.routes.projects import projects_bp


main_bp = Blueprint('main', __name__)

# main_bp.register_blueprint(projects_bp, url_prefix='/projects')

from webapp.routes import views