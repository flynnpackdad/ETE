"""
Service CRUD blueprint.

The Service is the anchor entity — 'I do these N things.' It holds
descriptive fields only; cost is derived from linked resources (Phase 2+).
"""
from flask import Blueprint, render_template, redirect, url_for, flash, abort
from flask_login import login_required

from . import db
from .models import Service
from .forms import ServiceForm

bp = Blueprint("services", __name__)


@bp.before_request
@login_required
def require_login():
    pass


@bp.route("/services")
def list_():
    all_services = (Service.query
                    .order_by(Service.sort_order, Service.name)
                    .all())
    return render_template("services/list.html", all_services=all_services)


@bp.route("/services/new", methods=["GET", "POST"])
def create():
    form = ServiceForm()
    if form.validate_on_submit():
        svc = Service(
            name=form.name.data.strip(),
            description=form.description.data,
            cost_drivers=form.cost_drivers.data,
            deliverables=form.deliverables.data,
            sort_order=form.sort_order.data or 0,
            is_active=form.is_active.data,
        )
        db.session.add(svc)
        db.session.commit()
        flash(f"Service '{svc.name}' created.", "success")
        return redirect(url_for("services.list_"))
    return render_template("services/form.html", form=form, title="New Service")


@bp.route("/services/<int:sid>")
def detail(sid):
    svc = db.session.get(Service, sid) or abort(404)
    return render_template("services/detail.html", svc=svc)


@bp.route("/services/<int:sid>/edit", methods=["GET", "POST"])
def edit(sid):
    svc = db.session.get(Service, sid) or abort(404)
    form = ServiceForm(obj=svc)
    if form.validate_on_submit():
        svc.name = form.name.data.strip()
        svc.description = form.description.data
        svc.cost_drivers = form.cost_drivers.data
        svc.deliverables = form.deliverables.data
        svc.sort_order = form.sort_order.data or 0
        svc.is_active = form.is_active.data
        db.session.commit()
        flash(f"Service '{svc.name}' updated.", "success")
        return redirect(url_for("services.detail", sid=svc.id))
    return render_template("services/form.html", form=form, svc=svc,
                           title=f"Edit: {svc.name}")


@bp.route("/services/<int:sid>/delete", methods=["POST"])
def delete(sid):
    svc = db.session.get(Service, sid) or abort(404)
    name = svc.name
    db.session.delete(svc)   # cascades to tools + links
    db.session.commit()
    flash(f"Service '{name}' deleted.", "info")
    return redirect(url_for("services.list_"))