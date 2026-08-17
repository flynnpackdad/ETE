"""
Phase 5 — HTML Export Blueprint

Generates a standalone, self-contained HTML presentation deck from live
database data.  The output mirrors the GoodLeap-branded slide-deck style
from the sample file (Sample/ETE IT Service Catalog.html).

Two routes:
    /export/catalog          — view the deck in-browser
    /export/catalog/download — download as a .html file
"""
from datetime import datetime

from flask import Blueprint, Response, render_template
from flask_login import login_required
from sqlalchemy import func

from .models import (
    Service, CostCenter, Vendor, Contractor, Employee,
    ResourceServiceLink, Resource, Tool, TimePoint,
)

bp = Blueprint("export", __name__, url_prefix="/export")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _fmt(n):
    """Format as dollar string with commas, no decimals."""
    return f"${n:,.0f}"


def _fmt_full(n):
    """Format as dollar string with 2 decimals."""
    return f"${n:,.2f}"


def _fmt_fte(n):
    """Format FTE to 2 decimal places."""
    return f"{n:.2f}"


# ---------------------------------------------------------------------------
# Data assembly
# ---------------------------------------------------------------------------

def _assemble_data():
    """Pull all data needed for the export deck from the database."""

    # --- Services with cost aggregation ---
    service_rows = (
        Service.query
        .outerjoin(ResourceServiceLink)
        .with_entities(
            Service.id,
            Service.name,
            Service.description,
            Service.cost_drivers,
            Service.deliverables,
            Service.sort_order,
            Service.is_active,
            func.coalesce(func.sum(ResourceServiceLink.current_amount), 0).label("total_cost"),
            func.coalesce(func.sum(ResourceServiceLink.current_fte), 0).label("total_fte"),
        )
        .filter_by(is_active=True)
        .group_by(
            Service.id, Service.name, Service.description,
            Service.cost_drivers, Service.deliverables,
            Service.sort_order, Service.is_active,
        )
        .order_by(Service.sort_order)
        .all()
    )

    services = []
    for s in service_rows:
        # Fetch tools for this service
        tools = Tool.query.filter_by(service_id=s.id).all()

        # Fetch linked resources with details
        links = (
            ResourceServiceLink.query
            .join(Resource)
            .filter(ResourceServiceLink.service_id == s.id)
            .all()
        )

        # Separate vendor spend vs labor cost
        vendor_spend = sum(
            l.current_amount for l in links if l.resource.kind == "vendor"
        )
        contractor_spend = sum(
            l.current_amount for l in links if l.resource.kind == "contractor"
        )
        labor_cost = sum(
            l.current_amount for l in links if l.resource.kind == "employee"
        )

        emp_fte = sum(
            l.current_fte for l in links if l.resource.kind == "employee"
        )
        ctr_fte = sum(
            l.current_fte for l in links if l.resource.kind == "contractor"
        )

        services.append({
            "id": s.id,
            "name": s.name,
            "description": s.description or "",
            "cost_drivers": [
                x.strip() for x in (s.cost_drivers or "").splitlines() if x.strip()
            ],
            "deliverables": [
                x.strip() for x in (s.deliverables or "").splitlines() if x.strip()
            ],
            "tools": [t.name for t in tools],
            "vendor_spend": vendor_spend,
            "contractor_spend": contractor_spend,
            "labor_cost": labor_cost,
            "total_cost": s.total_cost,
            "emp_fte": emp_fte,
            "ctr_fte": ctr_fte,
            "total_fte": s.total_fte,
            # Resources linked to this service
            "resources": [
                {
                    "name": l.resource.name,
                    "kind": l.resource.kind,
                    "cost_center": l.resource.cost_center.name if l.resource.cost_center else "",
                    "amount": l.current_amount,
                    "fte": l.current_fte,
                }
                for l in links
            ],
        })

    # --- Cost by Cost Center ---
    cc_rows = (
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

    cost_centers = [
        {
            "id": c.id,
            "name": c.name,
            "total_cost": c.total_cost,
            "total_fte": c.total_fte,
        }
        for c in cc_rows
    ]

    # --- Headcount ---
    vendor_count = Vendor.query.count()
    contractor_count = Contractor.query.count()
    employee_count = Employee.query.count()

    # --- Totals ---
    total_vendor_spend = sum(s["vendor_spend"] for s in services)
    total_contractor_spend = sum(s["contractor_spend"] for s in services)
    total_labor = sum(s["labor_cost"] for s in services)
    grand_total = sum(s["total_cost"] for s in services)
    total_emp_fte = sum(s["emp_fte"] for s in services)
    total_ctr_fte = sum(s["ctr_fte"] for s in services)
    total_fte = total_emp_fte + total_ctr_fte

    # --- Latest snapshot period ---
    latest_tp = TimePoint.query.order_by(TimePoint.period.desc()).first()
    latest_period = latest_tp.period if latest_tp else None

    # --- Generation timestamp ---
    generated_at = datetime.utcnow().strftime("%B %d, %Y at %I:%M %p UTC")

    return {
        "services": services,
        "cost_centers": cost_centers,
        "vendor_count": vendor_count,
        "contractor_count": contractor_count,
        "employee_count": employee_count,
        "total_vendor_spend": total_vendor_spend,
        "total_contractor_spend": total_contractor_spend,
        "total_labor": total_labor,
        "grand_total": grand_total,
        "total_emp_fte": total_emp_fte,
        "total_ctr_fte": total_ctr_fte,
        "total_fte": total_fte,
        "latest_period": latest_period,
        "generated_at": generated_at,
    }


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@bp.route("/catalog")
@login_required
def catalog_view():
    """Render the standalone HTML deck in the browser."""
    data = _assemble_data()
    return render_template("export/catalog.html", data=data)


@bp.route("/catalog/download")
@login_required
def catalog_download():
    """Download the standalone HTML deck as a file."""
    data = _assemble_data()
    html = render_template("export/catalog_standalone.html", data=data)
    filename = f"ETE_Service_Catalog_{datetime.utcnow().strftime('%Y-%m-%d')}.html"
    return Response(
        html,
        mimetype="text/html",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )