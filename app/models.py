"""
Domain models for the ETE Service Catalog.

Relationship map (Option A — cost lives on the Resource<->Service link):

    CostCenter 1--* Resource
    Service    *--* Resource   (via ResourceServiceLink, which carries cost)
    Vendor     1--* Contractor
    Service    1--* Tool
    ResourceServiceLink *--* TimePoint   (quarterly cost/FTE snapshots)

Resource is a base for the three cost-bearing types: Vendor, Contractor,
Employee. Each resource belongs to exactly one CostCenter and may be linked
to many Services. The link carries the cost allocation (Option A).
"""
from datetime import datetime

from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

from . import db, login_manager


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------
class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password):
        # Pin the method so hashing works across Python versions
        # (newer Werkzeug defaults to scrypt, which older OpenSSL lacks).
        self.password_hash = generate_password_hash(
            password, method="pbkdf2:sha256", salt_length=16
        )

    def check_password(self, password):
        if not self.password_hash:
            return False
        return check_password_hash(self.password_hash, password)


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


# ---------------------------------------------------------------------------
# Cost Center
# ---------------------------------------------------------------------------
class CostCenter(db.Model):
    """An independent cost dimension (e.g. IT Ops, IT Engineering).

    Cost centers apply to *resources* only — never directly to services.
    """
    __tablename__ = "cost_centers"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), unique=True, nullable=False)
    description = db.Column(db.Text, nullable=True)

    # Relationships
    vendors = db.relationship("Vendor", back_populates="cost_center")
    contractors = db.relationship("Contractor", back_populates="cost_center")
    employees = db.relationship("Employee", back_populates="cost_center")

    def __repr__(self):
        return f"<CostCenter {self.name}>"


# ---------------------------------------------------------------------------
# Service (the anchor entity)
# ---------------------------------------------------------------------------
class Service(db.Model):
    """The thing ETE delivers. 'I do these N things.'

    Holds descriptive fields only. Cost is NOT stored here directly — it is
    derived from the resources linked to this service (Option A).
    """
    __tablename__ = "services"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    cost_drivers = db.Column(db.Text, nullable=True)   # newline-separated
    deliverables = db.Column(db.Text, nullable=True)   # newline-separated
    is_active = db.Column(db.Boolean, default=True)
    sort_order = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    tools = db.relationship("Tool", back_populates="service",
                            cascade="all, delete-orphan")
    links = db.relationship("ResourceServiceLink", back_populates="service",
                            cascade="all, delete-orphan")

    # --- convenience accessors (descriptive lists) ---
    @property
    def cost_driver_list(self):
        return [x for x in (self.cost_drivers or "").splitlines() if x.strip()]

    @property
    def deliverable_list(self):
        return [x for x in (self.deliverables or "").splitlines() if x.strip()]

    def __repr__(self):
        return f"<Service {self.name}>"


# ---------------------------------------------------------------------------
# Resource base + concrete types
# ---------------------------------------------------------------------------
class Resource(db.Model):
    """Abstract base for cost-bearing resources.

    Uses SQLAlchemy single-table inheritance so that a single `resources`
    table holds vendors, contractors, and employees, and a resource can be
    linked to services uniformly via ResourceServiceLink.
    """
    __tablename__ = "resources"

    id = db.Column(db.Integer, primary_key=True)
    kind = db.Column(db.String(20), nullable=False)  # 'vendor' | 'contractor' | 'employee'
    name = db.Column(db.String(200), nullable=False)
    notes = db.Column(db.Text, nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Every resource books to exactly one cost center.
    cost_center_id = db.Column(db.Integer, db.ForeignKey("cost_centers.id"),
                               nullable=False)
    cost_center = db.relationship("CostCenter")

    # Polymorphic concrete classes
    __mapper_args__ = {
        "polymorphic_identity": "resource",
        "polymorphic_on": kind,
    }

    # Links to services (the cost-bearing relationships)
    links = db.relationship("ResourceServiceLink", back_populates="resource",
                            cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Resource {self.kind}:{self.name}>"


class Vendor(Resource):
    __mapper_args__ = {"polymorphic_identity": "vendor"}

    # A vendor's all-up cost is the sum of its link allocations (Option A).
    # Contractors roll up to a vendor.
    contractors = db.relationship("Contractor", back_populates="vendor",
                                  cascade="all, delete-orphan")
    # Tools associated with this vendor
    tools = db.relationship("Tool", back_populates="vendor")

    @property
    def all_up_cost(self):
        """Sum of current-period allocations across all service links."""
        return sum(l.current_amount for l in self.links)


class Contractor(Resource):
    __mapper_args__ = {"polymorphic_identity": "contractor"}

    # Contractors map back to a vendor (vendor holds the all-up cost).
    vendor_id = db.Column(db.Integer, db.ForeignKey("resources.id"),
                          nullable=True)
    vendor = db.relationship("Vendor", back_populates="contractors",
                             remote_side=[Resource.id])


class Employee(Resource):
    __mapper_args__ = {"polymorphic_identity": "employee"}

    # Full-time-equivalent allocation (0.0 - 1.0+).
    fte = db.Column(db.Float, default=1.0)


# ---------------------------------------------------------------------------
# ToolCategory (CRUD-able categories for tools, e.g., Hardware, Software, Circuit)
# ---------------------------------------------------------------------------
class ToolCategory(db.Model):
    __tablename__ = "tool_categories"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text, nullable=True)
    sort_order = db.Column(db.Integer, default=0)

    # Tools in this category
    tools = db.relationship("Tool", back_populates="category")
    def __repr__(self):
        return f"<ToolCategory {self.name}>"


# ---------------------------------------------------------------------------
# Tool (associates to services, M:1-ish)
# ---------------------------------------------------------------------------
class Tool(db.Model):
    __tablename__ = "tools"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    service_id = db.Column(db.Integer, db.ForeignKey("services.id"),
                           nullable=True)
    service = db.relationship("Service", back_populates="tools")
    vendor_id = db.Column(db.Integer, db.ForeignKey("resources.id"),
                          nullable=True)
    vendor = db.relationship("Vendor", back_populates="tools")

    # Budget projection fields
    category_id = db.Column(db.Integer, db.ForeignKey("tool_categories.id"), nullable=True)
    category = db.relationship("ToolCategory", back_populates="tools")
    projected_cost = db.Column(db.Float, default=0.0)
    cost_type = db.Column(db.String(20), default="one_time")  # "one_time" | "recurring_monthly" | "recurring_annual"
    def __repr__(self):
        return f"<Tool {self.name}>"


# ---------------------------------------------------------------------------
# Resource <-> Service link (Option A: cost lives HERE)
# ---------------------------------------------------------------------------
class ResourceServiceLink(db.Model):
    """Joins a Resource to a Service and carries the cost allocation.

    A vendor's all-up cost is split across its links; each link's
    `current_amount` is the allocation to that particular service.
    """
    __tablename__ = "resource_service_links"
    __table_args__ = (
        db.UniqueConstraint("resource_id", "service_id",
                            name="uq_resource_service"),
    )

    id = db.Column(db.Integer, primary_key=True)
    resource_id = db.Column(db.Integer, db.ForeignKey("resources.id"),
                            nullable=False)
    service_id = db.Column(db.Integer, db.ForeignKey("services.id"),
                           nullable=False)

    resource = db.relationship("Resource", back_populates="links")
    service = db.relationship("Service", back_populates="links")

    # Current allocation (the "now" value). Historical values live in
    # TimePoint rows.
    current_amount = db.Column(db.Float, default=0.0)
    current_fte = db.Column(db.Float, default=0.0)

    # Historical snapshots for trending (Phase 3).
    time_points = db.relationship("TimePoint", back_populates="link",
                                  cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Link {self.resource_id}->{self.service_id} ${self.current_amount}>"


# ---------------------------------------------------------------------------
# TimePoint (quarterly cost/FTE snapshots for trending)
# ---------------------------------------------------------------------------
class TimePoint(db.Model):
    """A dated snapshot of a link's cost/FTE for a given period.

    Period is a string like '2026-Q1'. Enables QoQ and YoY trending.
    """
    __tablename__ = "time_points"
    __table_args__ = (
        db.UniqueConstraint("link_id", "period", name="uq_link_period"),
    )

    id = db.Column(db.Integer, primary_key=True)
    link_id = db.Column(db.Integer, db.ForeignKey("resource_service_links.id"),
                        nullable=False)
    period = db.Column(db.String(8), nullable=False, index=True)  # e.g. '2026-Q1'
    amount = db.Column(db.Float, default=0.0)
    fte = db.Column(db.Float, default=0.0)
    recorded_at = db.Column(db.DateTime, default=datetime.utcnow)

    link = db.relationship("ResourceServiceLink", back_populates="time_points")

    def __repr__(self):
        return f"<TimePoint link={self.link_id} {self.period} ${self.amount}>"

