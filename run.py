"""
Entry point for the ETE Service Catalog.

Usage:
    export ETE_USERNAME="admin"
    export ETE_PASSWORD="your-password"
    export ETE_SECRET_KEY="a-long-random-string"
    python run.py

Then open http://127.0.0.1:5000
"""
from app import create_app

app = create_app()

if __name__ == "__main__":
    app.run(debug=True, host="127.0.0.1", port=15000)