from flask import Blueprint

bp = Blueprint('distance', __name__, template_folder='templates', static_folder='static')

from app.distance import routes