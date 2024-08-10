from flask import Blueprint

from webapp.routes.projects import projects_bp


main_bp = Blueprint('main', __name__)

main_bp.register_blueprint(projects_bp, url_prefix='/projects')

def import_routes():
    from webapp.routes import views
    from webapp.routes.projects.compound_interest import dash
    from webapp.routes.projects.education_journey import dash
    from webapp.routes.projects.portfolio_projection import dash