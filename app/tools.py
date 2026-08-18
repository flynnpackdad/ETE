"""
Tool CRUD blueprint.

Tools associate to services (M:1-ish). They are descriptive — not cost-bearing
resources — and represent the technology stack supporting each service.
"""
from flask import Blueprint, render_template, redirect, url_for, flash, abort
from flask_login import login_required
from sqlalchemy.orm import joinedload

from . import db
from .models import Tool, Service, Vendor, ToolCategory, CostCenter
from .forms import ToolForm

bp = Blueprint("tools", __name__)


def _populate_services(form):
    """Helper: fill the service_id dropdown."""
    form.service_id.choices = [
        (0, "--- Unassigned ---")
    ] + [
        (s.id, s.name) for s in Service.query.order_by(Service.name).all()
    ]


def _populate_vendors(form):
    """Helper: fill the vendor_id dropdown."""
    form.vendor_id.choices = [
        (0, "--- Unassigned ---")
    ] + [
        (v.id, v.name) for v in Vendor.query.order_by(Vendor.name).all()
    ]


def _populate_categories(form):
    """Helper: fill the category_id dropdown."""
    form.category_id.choices = [
        (0, "--- Unassigned ---")
    ] + [
        (c.id, c.name) for c in ToolCategory.query.order_by(ToolCategory.sort_order, ToolCategory.name).all()
    ]


def _populate_cost_centers(form):
    """Helper: fill the cost_center_id dropdown."""
    form.cost_center_id.choices = [
        (0, "--- Unassigned ---")
    ] + [
        (cc.id, cc.name) for cc in CostCenter.query.order_by(CostCenter.name).all()
    ]


@bp.before_request
@login_required
def require_login():
    pass


@bp.route("/tools")
def list_():
    tools = db.session.query(Tool).options(joinedload(Tool.vendor), joinedload(Tool.category)).order_by(Tool.name).all()
    return render_template("tools/list.html", tools=tools)


@bp.route("/tools/new", methods=["GET", "POST"])
def create():
    form = ToolForm()
    _populate_services(form)
    _populate_vendors(form)
    _populate_categories(form)
    _populate_cost_centers(form)
    if form.validate_on_submit():
        service_id = form.service_id.data or None
        vendor_id = form.vendor_id.data or None
        cost_center_id = form.cost_center_id.data or None
        category_id = form.category_id.data or None
        tool = Tool(
            name=form.name.data.strip(),
            service_id=service_id,
            vendor_id=vendor_id,
            cost_center_id=cost_center_id,
            category_id=category_id,
            projected_cost=form.projected_cost.data or 0.0,
            cost_type=form.cost_type.data or "one_time",
        )
        db.session.add(tool)
        db.session.commit()
        flash(f"Tool '{tool.name}' created.", "success")
        return redirect(url_for("tools.list_"))
    return render_template("tools/form.html", form=form, title="New Tool")


@bp.route("/tools/<int:tid>")
def detail(tid):
    tool = db.session.get(Tool, tid) or abort(404)
    return render_template("tools/detail.html", tool=tool)


@bp.route("/tools/<int:tid>/edit", methods=["GET", "POST"])
def edit(tid):
    tool = db.session.get(Tool, tid) or abort(404)
    form = ToolForm(obj=tool)
    _populate_services(form)
    _populate_vendors(form)
    _populate_categories(form)
    _populate_cost_centers(form)
    if form.validate_on_submit():
        tool.name = form.name.data.strip()
        tool.service_id = form.service_id.data or None
        tool.vendor_id = form.vendor_id.data or None
        tool.cost_center_id = form.cost_center_id.data or None
        tool.category_id = form.category_id.data or None
        tool.projected_cost = form.projected_cost.data or 0.0
        tool.cost_type = form.cost_type.data or "one_time"
        db.session.commit()
        flash(f"Tool '{tool.name}' updated.", "success")
        return redirect(url_for("tools.detail", tid=tool.id))
    return render_template(
        "tools/form.html", form=form, tool=tool,
        title=f"Edit: {tool.name}",
    )


@bp.route("/tools/<int:tid>/delete", methods=["POST"])
def delete(tid):
    tool = db.session.get(Tool, tid) or abort(404)
    name = tool.name
    db.session.delete(tool)
    db.session.commit()
    flash(f"Tool '{name}' deleted.", "info")
    return redirect(url_for("tools.list_"))