"""
Application configuration.

Secrets are read from environment variables so they never live in source
control. To run locally, export these in your shell before starting the app:

    export ETE_USERNAME="admin"
    export ETE_PASSWORD="your-password"
    export ETE_SECRET_KEY="a-long-random-string"
    export ETE_DATABASE="ete_catalog.db"   # optional, defaults shown below

Or put them in a shell wrapper / .env file loaded by your runner of choice.
"""
import os


class Config:
    # --- Flask core ---
    SECRET_KEY = os.environ.get("ETE_SECRET_KEY", "dev-insecure-key-change-me")
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"

    # --- Database (SQLite, single file, local) ---
    DB_PATH = os.environ.get("ETE_DATABASE", "ete_catalog.db")
    SQLALCHEMY_DATABASE_URI = "sqlite:///" + os.path.abspath(DB_PATH)
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # --- Single-user auth ---
    # The app is single-user. We compare the login against these env values.
    # The password is checked via werkzeug's secure comparator (constant-time).
    APP_USERNAME = os.environ.get("ETE_USERNAME", "admin")

    # Password is stored hashed. On first run, if no hash exists in the DB,
    # we hash the env password and persist it (see auth bootstrap).
    APP_PASSWORD = os.environ.get("ETE_PASSWORD", "")

    # --- App metadata ---
    APP_NAME = "ETE Service Catalog"
    ORG_NAME = "ETE"