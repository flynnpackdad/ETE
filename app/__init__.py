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
    from .auth import bp as auth_bp
    from .main import bp as main_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)

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
    from werkzeug.security import generate_password_hash

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