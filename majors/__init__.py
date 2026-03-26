from flask import Blueprint

majors_bp = Blueprint("majors", __name__, url_prefix="/majors")

from . import views