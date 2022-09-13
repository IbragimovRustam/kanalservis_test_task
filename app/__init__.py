from flask import Flask, request, redirect, url_for, current_app
from dashboards import basic_info
from config import Config

from flask_admin import Admin, AdminIndexView
from flask_admin.contrib.sqla import ModelView
from flask_admin.menu import MenuLink

from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

from dashboards import basic_info


db = SQLAlchemy()
migrate = Migrate()

admin = Admin(name='Каналсервис', index_view=AdminIndexView(), template_mode='bootstrap3')


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    with app.app_context():
        db.create_all()
    #     if db.engine.url.drivername == 'sqlite':
    #         migrate.init_app(app, db, render_as_batch=True)
    #     else:
    #         migrate.init_app(app, db)

    from app.models import Orders
    
    admin.init_app(app)
    admin.add_view(ModelView(Orders, db.session))
    admin.add_link(MenuLink(name='Main', category='', url='/'))

    from app.errors import bp as errors_bp
    app.register_blueprint(errors_bp)

    from app.main import bp as main_bp
    app.register_blueprint(main_bp)

    from app.dash import bp as dash_bp
    app.register_blueprint(dash_bp)

    app = basic_info.Add_Dash(app)

    return app


from app import models

