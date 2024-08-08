from flask import Blueprint

from webapp.routes.compound_interest.dash import comp_int_bp
from webapp.routes.education_journey.dash import edu_jou_bp
from webapp.routes.portfolio_projection.dash import port_proj_bp

main_bp = Blueprint('main', __name__)

main_bp.register_blueprint(comp_int_bp, url_prefix='/dash/compoundCalc')
main_bp.register_blueprint(edu_jou_bp, url_prefix='/dash/educationJourney')
main_bp.register_blueprint(port_proj_bp, url_prefix='/dash/portfolioProjection')