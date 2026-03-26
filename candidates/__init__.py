from flask import Blueprint

candidates_bp = Blueprint("candidates", __name__, url_prefix="/candidates")

from . import views