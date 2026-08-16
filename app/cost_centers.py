"""
Cost Center CRUD blueprint.

Cost centers are an independent dimension (IT Ops, IT Engineering). They
apply to resources only — never directly to services.
"""
from flask import Blueprint, render_template, redirect, url_for, flash, abort
from flask_login import login_required

from . import db
from .models import CostCenter
from .forms import CostCenterForm

bp = Blueprint("cost_centers", __name__)


@bp.before_request
@login_required
def require_login():
    pass


@bp.route("/cost-centers")
def list_():
    centers = CostCenter.query.order_by(CostCenter.name).all()
    return render_template("cost_centers/list.html", centers=centers)


@bp.route("/cost-centers/new", methods=["GET", "POST"])
def create():
    form = CostCenterForm()
    if form.validate_on_submit():
        existing = CostCenter.query.filter_by(
            name=form.name.data.strip()).first()
        if existing:
            form.name.errors.append(
                "A cost center with this name already exists.")
        else:
            cc = CostCenter(name=form.name.data.strip(),
                            description=form.description.data)
            db.session.add(cc)
            db.session.commit()
            flash(f"Cost center '{cc.name}' created.", "success")
            return redirect(url_for("cost_centers.list_"))
    return render_template("cost_centers/form.html", form=form,
                           title="New Cost Center")


@bp.route("/cost-centers/<int:cid>")
def detail(cid):
    cc = db.session.get(CostCenter, cid) or abort(404)
    return render_template("cost_centers/detail.html", cc=cc)


@bp.route("/cost-centers/<int:cid>/edit", methods=["GET", "POST"])
def edit(cid):
    cc = db.session.get(CostCenter, cid) or abort(404)
    form = CostCenterForm(obj=cc)
    if form.validate_on_submit():
        cc.name = form.name.data.strip()
        cc.description = form.description.data
        db.session.commit()
        flash(f"Cost center '{cc.name}' updated.", "success")
        return redirect(url_for("cost_centers.list_"))
    return render_template("cost_centers/form.html", form=form, cc=cc,
                           title=f"Edit: {cc.name}")


@bp.route("/cost-centers/<int:cid>/delete", methods=["POST"])
def delete(cid):
    cc = db.session.get(CostCenter, cid) or abort(404)
    name = cc.name
    if cc.vendors or cc.contractors or cc.employees:
        flash("This cost center has resources assigned to it and cannot be "
              "deleted. Reassign those resources first.", "danger")
    else:
        db.session.delete(cc)
        db.session.commit()
        flash(f"Cost center '{name}' deleted.", "info")
    return redirect(url_for("cost_centers.list_"))
