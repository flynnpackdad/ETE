"""
Contractor CRUD blueprint.

Contractors are cost-bearing resources that belong to a cost center
and optionally roll up to a vendor.
"""
from flask import Blueprint, render_template, redirect, url_for, flash, abort
from flask_login import login_required

from . import db
from .models import Contractor, CostCenter, Vendor, Service
from .forms import ContractorForm

bp = Blueprint("contractors", __name__)


def _populate_selects(form):
    """Helper: fill cost center and vendor dropdowns."""
    form.cost_center_id.choices = [
        (cc.id, cc.name) for cc in CostCenter.query.order_by(CostCenter.name).all()
    ]
    form.vendor_id.choices = [
        (0, "--- None ---")
    ] + [
        (v.id, v.name) for v in Vendor.query.order_by(Vendor.name).all()
    ]


@bp.before_request
@login_required
def require_login():
    pass


@bp.route("/contractors")
def list_():
    contractors = Contractor.query.order_by(Contractor.name).all()
    return render_template("contractors/list.html", contractors=contractors)


@bp.route("/contractors/new", methods=["GET", "POST"])
def create():
    form = ContractorForm()
    _populate_selects(form)
    if form.validate_on_submit():
        vendor_id = form.vendor_id.data or None
        contractor = Contractor(
            name=form.name.data.strip(),
            cost_center_id=form.cost_center_id.data,
            vendor_id=vendor_id,
            notes=form.notes.data,
            is_active=form.is_active.data,
        )
        db.session.add(contractor)
        db.session.commit()
        flash(f"Contractor '{contractor.name}' created.", "success")
        return redirect(url_for("contractors.list_"))
    return render_template(
        "contractors/form.html", form=form, title="New Contractor"
    )


@bp.route("/contractors/<int:cid>")
def detail(cid):
    contractor = db.session.get(Contractor, cid) or abort(404)
    return render_template(
        "contractors/detail.html", contractor=contractor,
        services=Service.query.order_by(Service.name).all(),
    )


@bp.route("/contractors/<int:cid>/edit", methods=["GET", "POST"])
def edit(cid):
    contractor = db.session.get(Contractor, cid) or abort(404)
    form = ContractorForm(obj=contractor)
    _populate_selects(form)
    if form.validate_on_submit():
        contractor.name = form.name.data.strip()
        contractor.cost_center_id = form.cost_center_id.data
        contractor.vendor_id = form.vendor_id.data or None
        contractor.notes = form.notes.data
        contractor.is_active = form.is_active.data
        db.session.commit()
        flash(f"Contractor '{contractor.name}' updated.", "success")
        return redirect(url_for("contractors.detail", cid=contractor.id))
    return render_template(
        "contractors/form.html", form=form, contractor=contractor,
        title=f"Edit: {contractor.name}",
    )


@bp.route("/contractors/<int:cid>/delete", methods=["POST"])
def delete(cid):
    contractor = db.session.get(Contractor, cid) or abort(404)
    name = contractor.name
    db.session.delete(contractor)  # cascades to links
    db.session.commit()
    flash(f"Contractor '{name}' deleted.", "info")
    return redirect(url_for("contractors.list_"))