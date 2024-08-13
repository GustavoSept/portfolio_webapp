from ...projects import projects_bp
from .dash import similarity_search

@projects_bp.get("/search_study/<term>")
def search_study(term):
    return similarity_search(term)