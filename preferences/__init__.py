from flask import Blueprint

preferences_bp = Blueprint("preferences", __name__, url_prefix="/preferences")

from . import views