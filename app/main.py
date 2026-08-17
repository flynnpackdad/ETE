from flask import Blueprint, render_template
from flask_login import login_required
from sqlalchemy import func
from .models import (
    Service, CostCenter, Vendor, Contractor, Employee,
    ResourceServiceLink, Resource, TimePoint,
)

bp = Blueprint("main", __name__)


def _fmt(n):
    """Format a number as a dollar string with commas, no decimals."""
    return f"${n:,.0f}"


def _fmt_fte(n):
    """Format an FTE number to 2 decimal places."""
    return f"{n:.2f}"


@bp.route("/")
@login_required
def dashboard():
    """Landing page with financial summary stats."""

    # --- Entity counts ---
    vendors = Vendor.query.count()
    contractors = Contractor.query.count()
    employees = Employee.query.count()
    active_services = Service.query.filter_by(is_active=True).count()

    # --- Cost by Service (current allocations) ---
    service_costs = (
        Service.query
        .outerjoin(ResourceServiceLink)
        .with_entities(
            Service.id,
            Service.name,
            Service.sort_order,
            func.coalesce(func.sum(ResourceServiceLink.current_amount), 0).label("total_cost"),
            func.coalesce(func.sum(ResourceServiceLink.current_fte), 0).label("total_fte"),
        )
        .group_by(Service.id, Service.name, Service.sort_order)
        .order_by(Service.sort_order)
        .all()
    )

    # Enrich with formatted strings for the template
    service_rows = []
    for sc in service_costs:
        service_rows.append({
            "id": sc.id,
            "name": sc.name,
            "total_cost": sc.total_cost,
            "total_cost_fmt": _fmt(sc.total_cost),
            "total_fte": sc.total_fte,
            "total_fte_fmt": _fmt_fte(sc.total_fte),
        })

    # --- Cost by Cost Center ---
    cc_costs = (
        CostCenter.query
        .join(Resource)
        .outerjoin(ResourceServiceLink, Resource.id == ResourceServiceLink.resource_id)
        .with_entities(
            CostCenter.id,
            CostCenter.name,
            func.coalesce(func.sum(ResourceServiceLink.current_amount), 0).label("total_cost"),
            func.coalesce(func.sum(ResourceServiceLink.current_fte), 0).label("total_fte"),
        )
        .group_by(CostCenter.id, CostCenter.name)
        .order_by(func.sum(ResourceServiceLink.current_amount).desc())
        .all()
    )

    cc_rows = []
    for cc in cc_costs:
        cc_rows.append({
            "id": cc.id,
            "name": cc.name,
            "total_cost": cc.total_cost,
            "total_cost_fmt": _fmt(cc.total_cost),
            "total_fte": cc.total_fte,
            "total_fte_fmt": _fmt_fte(cc.total_fte),
        })

    # --- Grand totals ---
    grand_total_cost = sum(sc.total_cost for sc in service_rows)
    grand_total_fte = sum(sc.total_fte for sc in service_rows)

    # --- Latest snapshot period (if any) ---
    latest_tp = TimePoint.query.order_by(TimePoint.period.desc()).first()
    latest_period = latest_tp.period if latest_tp else None

    # --- Chart data (pre-built lists for JS) ---
    chart_labels = [sc["name"] for sc in service_rows]
    chart_data = [sc["total_cost"] for sc in service_rows]

    return render_template(
        "main/dashboard.html",
        vendors=vendors,
        contractors=contractors,
        employees=employees,
        active_services=active_services,
        service_costs=service_rows,
        cc_costs=cc_rows,
        grand_total_cost=grand_total_cost,
        grand_total_cost_fmt=_fmt(grand_total_cost),
        grand_total_fte=grand_total_fte,
        grand_total_fte_fmt=_fmt_fte(grand_total_fte),
        latest_period=latest_period,
        chart_labels=chart_labels,
        chart_data=chart_data,
    )

