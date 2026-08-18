# Cost Roll-Up Fix: Tools to Vendors

## Problem

When costs were added to tools (via the `projected_cost` field), these costs were not rolling up to the associated vendor's "All-Up Cost" field. The vendor's cost calculation only included costs from service links (`ResourceServiceLink`), not from tools.

## Root Cause

The `Vendor.all_up_cost` property in `app/models.py` only calculated costs from service links:

```python
@property
def all_up_cost(self):
    """Sum of current-period allocations across all service links."""
    return sum(l.current_amount for l in self.links)
```

This did not include the `projected_cost` from tools associated with the vendor.

## Solution

Updated the `Vendor.all_up_cost` property to include both service link costs and tool costs:

```python
@property
def all_up_cost(self):
    """Sum of current-period allocations across all service links plus tool costs."""
    link_costs = sum(l.current_amount for l in self.links)
    tool_costs = sum(t.projected_cost for t in self.tools)
    return link_costs + tool_costs
```

## Changes Made

### 1. Core Model Change (`app/models.py`)

Modified the `Vendor.all_up_cost` property to calculate:
- **Link Costs**: Sum of `current_amount` from all `ResourceServiceLink` objects
- **Tool Costs**: Sum of `projected_cost` from all `Tool` objects associated with the vendor

### 2. Documentation Updates

- **README.md**: Updated to clarify that tools roll up to vendors
- **BUDGET_PROJECTION_IMPLEMENTATION.md**: Updated to explain the cost roll-up mechanism and added example SQL queries

## How It Works Now

When you add a cost to a tool and associate it with a vendor:

1. Create/edit a tool and set the `projected_cost` field
2. Assign the tool to a vendor via the `vendor_id` field
3. The vendor's "All-Up Cost" automatically includes this tool's cost

The vendor's total cost is now calculated as:
```
All-Up Cost = Sum of Service Link Costs + Sum of Tool Costs
```

## Impact

This change affects the following pages:
- **Vendor List** (`/vendors`): Shows updated "All-Up Cost" column
- **Vendor Detail** (`/vendors/<id>`): Shows updated "All-Up Cost" in details
- **Cost Center Detail** (`/cost_centers/<id>`): Shows updated vendor costs

## Testing

To verify the fix:

```bash
cd /Users/deckard/Documents/GitHub/ETE
.venv/bin/python -c "
from app import create_app
from app.models import Vendor, Tool

app = create_app()

with app.app_context():
    vendors = Vendor.query.all()
    for v in vendors:
        print(f'{v.name}: \${v.all_up_cost:,.2f}')
"
```

## Example

Before the fix:
- Tool: "Laptop Hardware" with cost $25,000 linked to Vendor "CDW"
- Vendor "CDW" All-Up Cost: $0.00 (incorrect)

After the fix:
- Tool: "Laptop Hardware" with cost $25,000 linked to Vendor "CDW"
- Vendor "CDW" All-Up Cost: $25,000.00 (correct)

## Future Enhancements

Potential improvements to consider:
1. Add a breakdown of link costs vs tool costs in the UI
2. Add a "Total Tool Costs" column to the vendor list view
3. Add filtering/sorting by tool costs
4. Add historical tracking for tool costs (similar to TimePoint for links)