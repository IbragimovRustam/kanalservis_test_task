from flask import Blueprint

bp = Blueprint('dash',
                __name__,
                # url_prefix='/dashes',
                template_folder='templates',
                static_folder='static',
                )

from app.dash import routes
