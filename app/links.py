"""
Resource-Service Link CRUD blueprint.

Manages the many-to-many relationship between Resources and Services,
carrying cost allocation (Option A).
"""
from flask import Blueprint, render_template, redirect, url_for, flash, abort
from flask_login import login_required

from . import db
from .models import ResourceServiceLink, Resource, Service
from .forms import ResourceServiceLinkForm

bp = Blueprint("links", __name__)


def _populate_selects(form, exclude_link_id=None):
    """Helper: fill resource and service dropdowns."""
    form.resource_id.choices = [
        (r.id, f"[{r.kind.title()}] {r.name}")
        for r in Resource.query.order_by(Resource.kind, Resource.name).all()
    ]
    form.service_id.choices = [
        (s.id, s.name) for s in Service.query.order_by(Service.name).all()
    ]


@bp.before_request
@login_required
def require_login():
    pass


@bp.route("/services/<int:sid>/links/new", methods=["GET", "POST"])
def create(sid):
    service = db.session.get(Service, sid) or abort(404)
    form = ResourceServiceLinkForm()
    form.service_id.data = sid
    _populate_selects(form)

    if form.validate_on_submit():
        # Check for duplicate
        existing = ResourceServiceLink.query.filter_by(
            resource_id=form.resource_id.data,
            service_id=form.service_id.data,
        ).first()
        if existing:
            form.resource_id.errors.append(
                "This resource is already linked to this service."
            )
        else:
            link = ResourceServiceLink(
                resource_id=form.resource_id.data,
                service_id=form.service_id.data,
                current_amount=form.current_amount.data or 0.0,
                current_fte=form.current_fte.data or 0.0,
            )
            db.session.add(link)
            db.session.commit()
            flash(f"Resource linked to '{service.name}'.", "success")
            return redirect(url_for("services.detail", sid=sid))

    return render_template(
        "links/form.html", form=form, service=service,
        title=f"Link Resource to {service.name}",
    )


@bp.route("/links/<int:lid>/edit", methods=["GET", "POST"])
def edit(lid):
    link = db.session.get(ResourceServiceLink, lid) or abort(404)
    form = ResourceServiceLinkForm(obj=link)
    _populate_selects(form, exclude_link_id=lid)

    if form.validate_on_submit():
        # Check for duplicate (excluding current link)
        existing = ResourceServiceLink.query.filter(
            ResourceServiceLink.resource_id == form.resource_id.data,
            ResourceServiceLink.service_id == form.service_id.data,
            ResourceServiceLink.id != lid,
        ).first()
        if existing:
            form.resource_id.errors.append(
                "This resource is already linked to this service."
            )
        else:
            link.resource_id = form.resource_id.data
            link.service_id = form.service_id.data
            link.current_amount = form.current_amount.data or 0.0
            link.current_fte = form.current_fte.data or 0.0
            db.session.commit()
            flash("Link updated.", "success")
            return redirect(url_for("services.detail", sid=link.service_id))

    return render_template(
        "links/form.html", form=form, link=link,
        title="Edit Link",
    )


@bp.route("/links/<int:lid>/delete", methods=["POST"])
def delete(lid):
    link = db.session.get(ResourceServiceLink, lid) or abort(404)
    service_id = link.service_id
    db.session.delete(link)
    db.session.commit()
    flash("Resource unlinked from service.", "info")
    return redirect(url_for("services.detail", sid=service_id))