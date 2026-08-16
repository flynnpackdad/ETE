"""
Main blueprint — dashboard and (later) CRUD + trends + export views.

Phase 0 provides the dashboard shell. Later phases fill in the real
aggregation, CRUD, trends, and export routes.
"""
from flask import Blueprint, render_template
from flask_login import login_required
from .models import Service, CostCenter

bp = Blueprint("main", __name__)


@bp.route("/")
@login_required
def dashboard():
    """Landing page with summary stats."""
    services = Service.query.all()
    cost_centers = CostCenter.query.all()
    return render_template(
        "main/dashboard.html",
        services=services,
        cost_centers=cost_centers,
    )
