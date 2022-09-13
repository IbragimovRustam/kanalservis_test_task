from app.dash import bp
from flask import render_template
from dashboards import basic_info

from app.models import Orders


@bp.route('/orders')
def dash_app_template():
    return render_template('dash/app.html', title='Каналсервис', dash_url = basic_info.url_base)


