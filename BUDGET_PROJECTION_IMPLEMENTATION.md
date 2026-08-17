# Budget Projection Implementation

## Overview

Extended the `Tool` model to support projected budgeting by adding:
- **Category** (via CRUD-able `ToolCategory` model)
- **Projected Cost** (numeric)
- **Cost Type** (one-time, recurring monthly, recurring annual)

This enables:
- Cost by vendor (via existing `Tool.vendor` relationship)
- Cost by category (via new `Tool.category` relationship)
- Cost type breakdown (Capex vs Opex)

---

## Changes Made

### 1. Database Schema

#### New Table: `tool_categories`
```python
class ToolCategory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text, nullable=True)
    sort_order = db.Column(db.Integer, default=0)
    tools = db.relationship("Tool", back_populates="category")
```

#### Updated Table: `tools`
Added columns:
- `category_id` (FK → `tool_categories.id`)
- `projected_cost` (Float, default 0.0)
- `cost_type` (String, default "one_time")

### 2. Seed Data

Created 6 default categories:
| Name | Sort Order | Description |
|------|------------|-------------|
| Hardware | 1 | Physical equipment (servers, switches, laptops) |
| Software | 2 | Licensing, subscriptions, SaaS |
| Network Circuit | 3 | WAN, MPLS, internet circuits, dark fiber |
| Cloud | 4 | Cloud infrastructure (AWS, Azure, GCP) |
| Professional Services | 5 | Consulting, implementation, migration |
| Support & Maintenance | 6 | Annual support contracts (ASC) |

### 3. UI Changes

#### New Pages
- `/tool_categories` — List all categories
- `/tool_categories/new` — Create new category
- `/tool_categories/<id>` — View category details
- `/tool_categories/<id>/edit` — Edit category
- `/tool_categories/<id>/delete` — Delete category

#### Updated Pages
- `/tools` — Added columns: Category, Cost Type, Projected Cost
- `/tools/new` — Added form fields: Category, Cost Type, Projected Cost
- `/tools/<id>/edit` — Added form fields: Category, Cost Type, Projected Cost
- `/tools/<id>` — Added detail fields: Category, Cost Type, Projected Cost

### 4. Navigation

Added "Tool Categories" link in sidebar (between Tools and Export sections).

---

## Usage

### For Administrators

1. **Manage Categories**
   - Navigate to "Tool Categories" in sidebar
   - Create/edit/delete categories as needed
   - Categories are sorted by `sort_order`, then alphabetically

2. **Assign Categories to Tools**
   - When creating/editing a tool, select a category from dropdown
   - Enter projected cost (e.g., 1500.00)
   - Select cost type (Capex/One-time, Monthly, Annual)

3. **View Budget Aggregates**
   - Tools list now shows category, cost type, and projected cost
   - Vendor page shows tools (and their costs) associated with that vendor
   - Future: Add dashboard views for cost-by-vendor and cost-by-category

### For Budget Planners

The data model supports:
- **Cost by Vendor**: Sum of `projected_cost` for tools linked to a vendor
- **Cost by Category**: Sum of `projected_cost` for tools in a category
- **Cost by Category + Cost Type**: e.g., "Hardware Capex" vs "Hardware Opex"

---

## Example Queries

### Cost by Vendor (SQL)
```sql
SELECT v.name, SUM(t.projected_cost) as total_cost
FROM tools t
JOIN resources v ON t.vendor_id = v.id
GROUP BY v.name
ORDER BY total_cost DESC;
```

### Cost by Category (SQL)
```sql
SELECT c.name, SUM(t.projected_cost) as total_cost
FROM tools t
LEFT JOIN tool_categories c ON t.category_id = c.id
GROUP BY c.name
ORDER BY total_cost DESC;
```

### Recurring vs One-time (SQL)
```sql
SELECT 
    t.cost_type,
    SUM(t.projected_cost) as total_cost,
    COUNT(*) as tool_count
FROM tools t
GROUP BY t.cost_type;
```

---

## Next Steps (Future)

1. **Dashboard Views**
   - Cost by vendor chart
   - Cost by category chart
   - Recurring vs one-time breakdown

2. **Export Functionality**
   - Export tool list with cost fields to CSV/Excel
   - Export budget summary report

3. **Time-based Budgeting**
   - Track projected_cost over time (like TimePoint for links)
   - Compare budget vs actual spend

4. **Validation**
   - Prevent duplicate category names
   - Enforce positive projected_cost
   - Validate cost_type values

---

## Files Modified

| File | Change |
|------|--------|
| `app/models.py` | Added `ToolCategory` model; added columns to `Tool` |
| `app/forms.py` | Added `ToolCategoryForm`; extended `ToolForm` |
| `app/tools.py` | Updated to populate category dropdown; save category/cost fields |
| `app/tool_categories.py` | **NEW** — CRUD blueprint for tool categories |
| `app/__init__.py` | Registered `tool_categories` blueprint |
| `app/templates/base.html` | Added navigation link for Tool Categories |
| `app/templates/tools/list.html` | Added columns: Category, Cost Type, Projected Cost |
| `app/templates/tools/detail.html` | Added detail fields: Category, Cost Type, Projected Cost |
| `app/templates/tools/form.html` | Added form fields: Category, Cost Type, Projected Cost |
| `app/templates/tool_categories/*` | **NEW** — List, detail, form templates |
| `app/seed_tool_categories.py` | **NEW** — Seed script for default categories |

---

## Testing

Run the app:
```bash
cd /Users/deckard/Documents/GitHub/ETE
python3 -m flask --app app run --port 5001
```

Navigate to:
- http://localhost:5001/tool_categories — Manage categories
- http://localhost:5001/tools — View/edit tools with budget fields

Seed categories (run once):
```bash
python3 -m app.seed_tool_categories
```