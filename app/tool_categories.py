"""
ToolCategory CRUD blueprint.

Provides CRUD for tool categories (e.g., Hardware, Software, Network Circuit)
used to classify tools for budget projection.
"""
from flask import Blueprint, render_template, redirect, url_for, flash, abort
from flask_login import login_required

from . import db
from .models import ToolCategory
from .forms import ToolCategoryForm

bp = Blueprint("tool_categories", __name__)


@bp.before_request
@login_required
def require_login():
    pass


@bp.route("/tool_categories")
def list_():
    categories = ToolCategory.query.order_by(ToolCategory.sort_order, ToolCategory.name).all()
    return render_template("tool_categories/list.html", categories=categories)


@bp.route("/tool_categories/new", methods=["GET", "POST"])
def create():
    form = ToolCategoryForm()
    if form.validate_on_submit():
        category = ToolCategory(
            name=form.name.data.strip(),
            description=form.description.data.strip() if form.description.data else None,
            sort_order=form.sort_order.data or 0,
        )
        db.session.add(category)
        db.session.commit()
        flash(f"Category '{category.name}' created.", "success")
        return redirect(url_for("tool_categories.list_"))
    return render_template("tool_categories/form.html", form=form, title="New Category")


@bp.route("/tool_categories/<int:cid>")
def detail(cid):
    category = db.session.get(ToolCategory, cid) or abort(404)
    return render_template("tool_categories/detail.html", category=category)


@bp.route("/tool_categories/<int:cid>/edit", methods=["GET", "POST"])
def edit(cid):
    category = db.session.get(ToolCategory, cid) or abort(404)
    form = ToolCategoryForm(obj=category)
    if form.validate_on_submit():
        category.name = form.name.data.strip()
        category.description = form.description.data.strip() if form.description.data else None
        category.sort_order = form.sort_order.data or 0
        db.session.commit()
        flash(f"Category '{category.name}' updated.", "success")
        return redirect(url_for("tool_categories.detail", cid=category.id))
    return render_template(
        "tool_categories/form.html", form=form, category=category,
        title=f"Edit: {category.name}",
    )


@bp.route("/tool_categories/<int:cid>/delete", methods=["POST"])
def delete(cid):
    category = db.session.get(ToolCategory, cid) or abort(404)
    name = category.name
    db.session.delete(category)
    db.session.commit()
    flash(f"Category '{name}' deleted.", "info")
    return redirect(url_for("tool_categories.list_"))