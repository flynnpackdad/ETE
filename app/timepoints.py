"""
TimePoint CRUD + snapshot + trending blueprint.

TimePoints are quarterly cost/FTE snapshots per ResourceServiceLink,
enabling QoQ and YoY trending.
"""
from datetime import datetime
from flask import Blueprint, render_template, redirect, url_for, flash, abort, request
from flask_login import login_required

from . import db
from .models import TimePoint, ResourceServiceLink, Resource, Service
from .forms import TimePointForm, PeriodSnapshotForm

bp = Blueprint("timepoints", __name__)


# ---------------------------------------------------------------------------
# Period helpers
# ---------------------------------------------------------------------------

def _period_choices():
    """Return (value, label) pairs for the period dropdown.

    Shows all existing periods plus the current quarter as a suggestion.
    """
    existing = db.session.query(TimePoint.period).distinct().order_by(
        TimePoint.period.desc()
    ).all()
    periods = [p[0] for p in existing]

    # Current quarter
    now = datetime.utcnow()
    q = (now.month - 1) // 3 + 1
    current = f"{now.year}-Q{q}"
    if current not in periods:
        periods.insert(0, current)

    return [(p, p) for p in periods]


def _parse_period(period):
    """Parse 'YYYY-QN' into (year, quarter)."""
    try:
        year_str, q_str = period.split("-Q")
        return int(year_str), int(q_str)
    except (ValueError, AttributeError):
        return None, None


def _qoq_delta(period):
    """Return the previous quarter string, or None."""
    year, q = _parse_period(period)
    if q is None:
        return None
    if q == 1:
        return f"{year - 1}-Q4"
    return f"{year}-Q{q - 1}"


def _yoy_period(period):
    """Return the same quarter in the prior year, or None."""
    year, q = _parse_period(period)
    if q is None:
        return None
    return f"{year - 1}-Q{q}"


def _delta(current, previous):
    """Return (absolute, percent) delta. Handles None/zero gracefully."""
    if previous is None or previous == 0:
        return (current or 0, None)
    abs_delta = (current or 0) - previous
    pct = (abs_delta / previous) * 100
    return (abs_delta, pct)


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@bp.before_request
@login_required
def require_login():
    pass


@bp.route("/timepoints")
def list_():
    """Global timepoint list, optionally filtered by period."""
    period_filter = request.args.get("period")
    query = TimePoint.query.join(
        ResourceServiceLink
    ).join(
        Resource, ResourceServiceLink.resource_id == Resource.id
    ).join(
        Service, ResourceServiceLink.service_id == Service.id
    ).order_by(
        TimePoint.period.desc(),
        Resource.name,
        Service.name,
    )
    if period_filter:
        query = query.filter(TimePoint.period == period_filter)

    timepoints = query.all()
    all_periods = [p[0] for p in TimePoint.query.with_entities(
        TimePoint.period
    ).distinct().order_by(TimePoint.period.desc()).all()]

    return render_template(
        "timepoints/list.html",
        timepoints=timepoints,
        all_periods=all_periods,
        active_period=period_filter,
    )


@bp.route("/links/<int:lid>/history")
def link_history(lid):
    """Per-link trend view with Chart.js chart."""
    link = db.session.get(ResourceServiceLink, lid) or abort(404)
    points = (TimePoint.query
              .filter_by(link_id=lid)
              .order_by(TimePoint.period)
              .all())

    # Build series data for Chart.js
    labels = [p.period for p in points]
    amounts = [p.amount for p in points]
    ftes = [p.fte for p in points]

    # Build a lookup of period → amount for QoQ/YoY calculations
    amount_map = {p.period: p.amount for p in points}

    # Enrich each point with QoQ and YoY deltas
    enriched = []
    for p in points:
        qoq_prev = _qoq_delta(p.period)
        yoy_prev = _yoy_period(p.period)

        qoq_abs = None
        qoq_pct = None
        if qoq_prev in amount_map and amount_map[qoq_prev] != 0:
            qoq_abs = p.amount - amount_map[qoq_prev]
            qoq_pct = (qoq_abs / amount_map[qoq_prev]) * 100
        elif qoq_prev in amount_map:
            qoq_abs = 0

        yoy_abs = None
        yoy_pct = None
        if yoy_prev in amount_map and amount_map[yoy_prev] != 0:
            yoy_abs = p.amount - amount_map[yoy_prev]
            yoy_pct = (yoy_abs / amount_map[yoy_prev]) * 100
        elif yoy_prev in amount_map:
            yoy_abs = 0

        enriched.append({
            "tp": p,
            "qoq_abs": qoq_abs,
            "qoq_pct": qoq_pct,
            "yoy_abs": yoy_abs,
            "yoy_pct": yoy_pct,
        })

    return render_template(
        "timepoints/link_history.html",
        link=link, points=enriched,
        labels=labels, amounts=amounts, ftes=ftes,
    )


@bp.route("/links/<int:lid>/snapshot", methods=["GET", "POST"])
def add_snapshot(lid):
    """Add a single timepoint to a link."""
    link = db.session.get(ResourceServiceLink, lid) or abort(404)
    form = TimePointForm()
    form.period.choices = _period_choices()

    if form.validate_on_submit():
        # Check for duplicate
        existing = TimePoint.query.filter_by(
            link_id=lid, period=form.period.data,
        ).first()
        if existing:
            form.period.errors.append(
                "A snapshot for this period already exists."
            )
        else:
            tp = TimePoint(
                link_id=lid,
                period=form.period.data,
                amount=form.amount.data or 0.0,
                fte=form.fte.data or 0.0,
            )
            db.session.add(tp)
            db.session.commit()
            flash(f"Snapshot recorded for {form.period.data}.", "success")
            return redirect(url_for("timepoints.link_history", lid=lid))

    return render_template(
        "timepoints/form.html", form=form, link=link,
        title=f"Add Snapshot — {link.resource.name} → {link.service.name}",
    )


@bp.route("/timepoints/<int:tpid>/edit", methods=["GET", "POST"])
def edit(tpid):
    """Edit an existing timepoint."""
    tp = db.session.get(TimePoint, tpid) or abort(404)
    form = TimePointForm(obj=tp)
    form.period.choices = _period_choices()

    if form.validate_on_submit():
        # Check for duplicate (excluding current)
        existing = TimePoint.query.filter(
            TimePoint.link_id == tp.link_id,
            TimePoint.period == form.period.data,
            TimePoint.id != tpid,
        ).first()
        if existing:
            form.period.errors.append(
                "A snapshot for this period already exists on this link."
            )
        else:
            tp.period = form.period.data
            tp.amount = form.amount.data or 0.0
            tp.fte = form.fte.data or 0.0
            db.session.commit()
            flash("Snapshot updated.", "success")
            return redirect(url_for("timepoints.link_history", lid=tp.link_id))

    return render_template(
        "timepoints/form.html", form=form, tp=tp,
        title=f"Edit Snapshot — {tp.period}",
    )


@bp.route("/timepoints/<int:tpid>/delete", methods=["POST"])
def delete(tpid):
    tp = db.session.get(TimePoint, tpid) or abort(404)
    link_id = tp.link_id
    db.session.delete(tp)
    db.session.commit()
    flash("Snapshot deleted.", "info")
    return redirect(url_for("timepoints.link_history", lid=link_id))


@bp.route("/snapshots/period", methods=["GET", "POST"])
def period_snapshot():
    """Bulk snapshot: capture all current link values for a given period."""
    form = PeriodSnapshotForm()
    form.period.choices = _period_choices()

    if form.validate_on_submit():
        period = form.period.data
        links = ResourceServiceLink.query.all()
        created = 0
        skipped = 0
        for link in links:
            existing = TimePoint.query.filter_by(
                link_id=link.id, period=period,
            ).first()
            if existing:
                skipped += 1
            else:
                tp = TimePoint(
                    link_id=link.id,
                    period=period,
                    amount=link.current_amount or 0.0,
                    fte=link.current_fte or 0.0,
                )
                db.session.add(tp)
                created += 1

        db.session.commit()
        flash(
            f"Snapshot for {period}: {created} recorded, {skipped} already existed.",
            "success",
        )
        return redirect(url_for("timepoints.list_", period=period))

    return render_template(
        "timepoints/period_snapshot.html", form=form,
        title="Take Period Snapshot",
    )