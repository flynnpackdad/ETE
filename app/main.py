"""
Main blueprint — dashboard and (later) CRUD + trends + export views.

Phase 0 provides the dashboard shell. Later phases fill in the real
aggregation, CRUD, trends, and export routes.
"""
from flask import Blueprint, render_template
from flask_login import login_required

bp = Blueprint("main", __name__)


@bp.route("/")
@login_required
def dashboard():
    """Landing page. Phase 0 shows a placeholder; later phases add rollups."""
    return render_template("main/dashboard.html")