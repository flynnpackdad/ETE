"""
WTForms for the ETE Service Catalog.

Phase 1: CostCenterForm, ServiceForm.
Later phases add resource/link/time-point forms.
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