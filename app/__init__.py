"""
ETE Service Catalog — application factory.

Wires together Flask, SQLAlchemy, Login, and the blueprints.
Run with:  flask --app app run
"""
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

from config import Config

db = SQLAlchemy()
login_manager = LoginManager()


def create_app(config_object=Config):
    app = Flask(__name__)
    app.config.from_object(config_object)

    # Extensions
    db.init_app(app)
    login_manager.init_app(app)

    # LoginManager messaging
    login_manager.login_view = "auth.login"
    login_manager.login_message = "Please log in to access the catalog."
    login_manager.login_message_category = "info"

    # Blueprints
    from .auth import bp as auth_bp, csrf
    from .main import bp as main_bp
    from .cost_centers import bp as cost_centers_bp
    from .services import bp as services_bp
    from .vendors import bp as vendors_bp
    from .contractors import bp as contractors_bp
    from .employees import bp as employees_bp
    from .links import bp as links_bp
    from .tools import bp as tools_bp
    from .timepoints import bp as timepoints_bp
    from .export import bp as export_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(cost_centers_bp)
    app.register_blueprint(services_bp)
    app.register_blueprint(vendors_bp)
    app.register_blueprint(contractors_bp)
    app.register_blueprint(employees_bp)
    app.register_blueprint(links_bp)
    app.register_blueprint(tools_bp)
    app.register_blueprint(timepoints_bp)
    app.register_blueprint(export_bp)

    # Global CSRF protection (respects @csrf.exempt on the login route)
    csrf.init_app(app)

    # Create tables on first run.
    with app.app_context():
        db.create_all()
        _bootstrap_user(app)

    return app


def _bootstrap_user(app):
    """
    Single-user bootstrap: ensure a User row exists whose password hash
    matches the configured env password. If the env password changes, we
    update the stored hash so the next login uses the new credential.
    """
    from .models import User

    username = app.config["APP_USERNAME"]
    password = app.config["APP_PASSWORD"]

    user = User.query.filter_by(username=username).first()
    if user is None:
        if not password:
            app.logger.warning(
                "No ETE_PASSWORD set in environment; creating user '%s' "
                "with no password. Set ETE_PASSWORD to enable login.",
                username,
            )
        user = User(username=username)
        if password:
            user.set_password(password)
        db.session.add(user)
        db.session.commit()
        app.logger.info("Bootstrapped user '%s'.", username)
    else:
        # Keep the stored hash in sync with the env password if provided.
        if password and not user.check_password(password):
            user.set_password(password)
            db.session.commit()
            app.logger.info("Updated password for user '%s'.", username)