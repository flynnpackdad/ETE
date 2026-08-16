# ETE

A single-user, locally-hosted Flask web app for the Head of ETE to manage the
IT service catalog and track how costs and resources change over time
(quarter-over-quarter and year-over-year), with the ability to export a
leadership-ready HTML presentation.

## The model (Option A)

- **Service** — the anchor. "I do these N things." Holds descriptive fields.
- **CostCenter** — independent dimension (IT Ops, IT Engineering). Applies to resources only.
- **Resources** (Vendor / Contractor / Employee) — each books to one CostCenter and links to many Services.
  - Contractors roll up to a Vendor (vendor holds all-up cost).
- **ResourceServiceLink** — joins a resource to a service and **carries the cost** (Option A). A vendor's all-up cost is split across its links.
- **TimePoint** — quarterly cost/FTE snapshots per link, for trending.
- **Tool** — associates to services.

## Stack

Flask · Jinja (server-rendered) · WTForms · SQLAlchemy · SQLite · Chart.js (trends, Phase 3)

## Setup
