"""
WTForms for the ETE Service Catalog.

Phase 1: CostCenterForm, ServiceForm.
Phase 2: VendorForm, ContractorForm, EmployeeForm, ResourceServiceLinkForm, ToolForm.
Phase 3: TimePointForm, PeriodSnapshotForm.
"""
from flask_wtf import FlaskForm
from wtforms import (
    StringField, TextAreaField, FloatField, BooleanField,
    SelectField, IntegerField,
)
from wtforms.validators import DataRequired, Optional, NumberRange


class CostCenterForm(FlaskForm):
    name = StringField("Name", validators=[DataRequired()])
    description = TextAreaField("Description", validators=[Optional()])


class ServiceForm(FlaskForm):
    name = StringField("Name", validators=[DataRequired()])
    description = TextAreaField("Description", validators=[Optional()])
    cost_drivers = TextAreaField(
        "Cost Drivers",
        validators=[Optional()],
        render_kw={"placeholder": "One cost driver per line"},
    )
    deliverables = TextAreaField(
        "Deliverables",
        validators=[Optional()],
        render_kw={"placeholder": "One deliverable per line"},
    )
    sort_order = IntegerField("Sort order", validators=[Optional()], default=0)
    is_active = BooleanField("Active", default=True)


# ---------------------------------------------------------------------------
# Phase 2 — Resource forms
# ---------------------------------------------------------------------------
class VendorForm(FlaskForm):
    name = StringField("Name", validators=[DataRequired()])
    cost_center_id = SelectField(
        "Cost Center", coerce=int, validators=[DataRequired()]
    )
    notes = TextAreaField("Notes", validators=[Optional()])
    is_active = BooleanField("Active", default=True)


class ContractorForm(FlaskForm):
    name = StringField("Name", validators=[DataRequired()])
    cost_center_id = SelectField(
        "Cost Center", coerce=int, validators=[DataRequired()]
    )
    vendor_id = SelectField(
        "Vendor (optional)", coerce=int, validators=[Optional()]
    )
    notes = TextAreaField("Notes", validators=[Optional()])
    is_active = BooleanField("Active", default=True)


class EmployeeForm(FlaskForm):
    name = StringField("Name", validators=[DataRequired()])
    cost_center_id = SelectField(
        "Cost Center", coerce=int, validators=[DataRequired()]
    )
    fte = FloatField(
        "FTE", validators=[Optional(), NumberRange(min=0.0, max=2.0)],
        default=1.0,
    )
    notes = TextAreaField("Notes", validators=[Optional()])
    is_active = BooleanField("Active", default=True)


class ResourceServiceLinkForm(FlaskForm):
    resource_id = SelectField(
        "Resource", coerce=int, validators=[DataRequired()]
    )
    service_id = SelectField(
        "Service", coerce=int, validators=[DataRequired()]
    )
    current_amount = FloatField(
        "Annual Cost ($)", validators=[Optional(), NumberRange(min=0)],
        default=0.0,
    )
    current_fte = FloatField(
        "FTE Allocation", validators=[Optional(), NumberRange(min=0)],
        default=0.0,
    )


class ToolForm(FlaskForm):
    name = StringField("Name", validators=[DataRequired()])
    service_id = SelectField(
        "Service (optional)", coerce=int, validators=[Optional()]
    )


# ---------------------------------------------------------------------------
# Phase 3 — Time tracking forms
# ---------------------------------------------------------------------------
class TimePointForm(FlaskForm):
    period = SelectField(
        "Period", coerce=str, validators=[DataRequired()],
        render_kw={"placeholder": "e.g. 2025-Q4"},
    )
    amount = FloatField(
        "Annual Cost ($)", validators=[Optional(), NumberRange(min=0)],
        default=0.0,
    )
    fte = FloatField(
        "FTE", validators=[Optional(), NumberRange(min=0)],
        default=0.0,
    )


class PeriodSnapshotForm(FlaskForm):
    period = SelectField(
        "Period", coerce=str, validators=[DataRequired()],
    )
