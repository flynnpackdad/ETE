"""
Employee CRUD blueprint.

Employees are cost-bearing resources that belong to a cost center
and carry an FTE value.
"""
from flask import Blueprint, render_template, redirect, url_for, flash, abort
from flask_login import login_required

from . import db
from .models import Employee, CostCenter, Service
from .forms import EmployeeForm

bp = Blueprint("employees", __name__)


def _populate_cost_centers(form):
    """Helper: fill the cost_center_id dropdown."""
    form.cost_center_id.choices = [
        (cc.id, cc.name) for cc in CostCenter.query.order_by(CostCenter.name).all()
    ]


@bp.before_request
@login_required
def require_login():
    pass


@bp.route("/employees")
def list_():
    employees = Employee.query.order_by(Employee.name).all()
    return render_template("employees/list.html", employees=employees)


@bp.route("/employees/new", methods=["GET", "POST"])
def create():
    form = EmployeeForm()
    _populate_cost_centers(form)
    if form.validate_on_submit():
        employee = Employee(
            name=form.name.data.strip(),
            cost_center_id=form.cost_center_id.data,
            fte=form.fte.data or 1.0,
            notes=form.notes.data,
            is_active=form.is_active.data,
        )
        db.session.add(employee)
        db.session.commit()
        flash(f"Employee '{employee.name}' created.", "success")
        return redirect(url_for("employees.list_"))
    return render_template(
        "employees/form.html", form=form, title="New Employee"
    )


@bp.route("/employees/<int:eid>")
def detail(eid):
    employee = db.session.get(Employee, eid) or abort(404)
    return render_template(
        "employees/detail.html", employee=employee,
        services=Service.query.order_by(Service.name).all(),
    )


@bp.route("/employees/<int:eid>/edit", methods=["GET", "POST"])
def edit(eid):
    employee = db.session.get(Employee, eid) or abort(404)
    form = EmployeeForm(obj=employee)
    _populate_cost_centers(form)
    if form.validate_on_submit():
        employee.name = form.name.data.strip()
        employee.cost_center_id = form.cost_center_id.data
        employee.fte = form.fte.data or 1.0
        employee.notes = form.notes.data
        employee.is_active = form.is_active.data
        db.session.commit()
        flash(f"Employee '{employee.name}' updated.", "success")
        return redirect(url_for("employees.detail", eid=employee.id))
    return render_template(
        "employees/form.html", form=form, employee=employee,
        title=f"Edit: {employee.name}",
    )


@bp.route("/employees/<int:eid>/delete", methods=["POST"])
def delete(eid):
    employee = db.session.get(Employee, eid) or abort(404)
    name = employee.name
    db.session.delete(employee)  # cascades to links
    db.session.commit()
    flash(f"Employee '{name}' deleted.", "info")
    return redirect(url_for("employees.list_"))