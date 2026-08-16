"""
Vendor CRUD blueprint.

Vendors are cost-bearing resources that belong to a cost center.
Contractors roll up to vendors.
"""
from flask import Blueprint, render_template, redirect, url_for, flash, abort
from flask_login import login_required

from . import db
from .models import Vendor, CostCenter, Service
from .forms import VendorForm

bp = Blueprint("vendors", __name__)


def _populate_cost_centers(form):
    """Helper: fill the cost_center_id dropdown."""
    form.cost_center_id.choices = [
        (cc.id, cc.name) for cc in CostCenter.query.order_by(CostCenter.name).all()
    ]


@bp.before_request
@login_required
def require_login():
    pass


@bp.route("/vendors")
def list_():
    vendors = Vendor.query.order_by(Vendor.name).all()
    return render_template("vendors/list.html", vendors=vendors)


@bp.route("/vendors/new", methods=["GET", "POST"])
def create():
    form = VendorForm()
    _populate_cost_centers(form)
    if form.validate_on_submit():
        vendor = Vendor(
            name=form.name.data.strip(),
            cost_center_id=form.cost_center_id.data,
            notes=form.notes.data,
            is_active=form.is_active.data,
        )
        db.session.add(vendor)
        db.session.commit()
        flash(f"Vendor '{vendor.name}' created.", "success")
        return redirect(url_for("vendors.list_"))
    return render_template("vendors/form.html", form=form, title="New Vendor")


@bp.route("/vendors/<int:vid>")
def detail(vid):
    vendor = db.session.get(Vendor, vid) or abort(404)
    return render_template(
        "vendors/detail.html", vendor=vendor,
        services=Service.query.order_by(Service.name).all(),
    )


@bp.route("/vendors/<int:vid>/edit", methods=["GET", "POST"])
def edit(vid):
    vendor = db.session.get(Vendor, vid) or abort(404)
    form = VendorForm(obj=vendor)
    _populate_cost_centers(form)
    if form.validate_on_submit():
        vendor.name = form.name.data.strip()
        vendor.cost_center_id = form.cost_center_id.data
        vendor.notes = form.notes.data
        vendor.is_active = form.is_active.data
        db.session.commit()
        flash(f"Vendor '{vendor.name}' updated.", "success")
        return redirect(url_for("vendors.detail", vid=vendor.id))
    return render_template(
        "vendors/form.html", form=form, vendor=vendor,
        title=f"Edit: {vendor.name}",
    )


@bp.route("/vendors/<int:vid>/delete", methods=["POST"])
def delete(vid):
    vendor = db.session.get(Vendor, vid) or abort(404)
    name = vendor.name
    db.session.delete(vendor)  # cascades to contractors + links
    db.session.commit()
    flash(f"Vendor '{name}' deleted.", "info")
    return redirect(url_for("vendors.list_"))