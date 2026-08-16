from flask import Blueprint, render_template
from flask_login import login_required
from .models import Service, CostCenter, Vendor, Contractor, Employee

bp = Blueprint("main", __name__)


@bp.route("/")
@login_required
def dashboard():
    """Landing page with summary stats."""
    services = Service.query.all()
    cost_centers = CostCenter.query.all()
    vendors = Vendor.query.all()
    contractors = Contractor.query.all()
    employees = Employee.query.all()
    return render_template(
        "main/dashboard.html",
        services=services,
        cost_centers=cost_centers,
        vendors=vendors,
        contractors=contractors,
        employees=employees,
    )
