
---

# MODEL.md

## Overview

I kept the data model intentionally small. The assignment felt more about handling messy ingestion and review workflows than building a huge ESG platform, so I focused on traceability and normalization first.

Main relationships:

```text id="fzjlkv"
Company
  └── UserProfile
  └── DataSource
       └── EmissionRecord
            └── AuditLog
```

The idea is:

* one company uploads data
* each upload becomes a batch (`DataSource`)
* each row becomes an `EmissionRecord`
* analyst actions get tracked in `AuditLog`

I wanted the flow to stay easy to reason about instead of introducing too many abstractions.

---

## Company

Represents a client organization.

Every user, upload, and emission record is tied back to a company. Multi-tenancy is enforced in the Django ORM layer using filters based on the logged-in user’s company.

I considered more advanced approaches like Postgres row-level security, but for this assignment it felt unnecessary complexity.

The model also includes a `slug` field mainly for cleaner URLs later if needed.

One thing this prototype does not properly handle is concurrent analyst workflows. If two analysts review the same row at the same time, the latest update wins.

---

## UserProfile

This extends Django’s built-in `User` model with a company relationship.

I kept auth intentionally simple:

* one analyst belongs to one company
* no advanced RBAC
* no multi-company access

If the system expanded later, this is where roles and permissions would grow.

---

## DataSource

Each uploaded CSV creates one `DataSource`.

This acts like a batch header and stores:

* upload metadata
* source type
* counts for failed/suspicious rows
* filename
* who uploaded it

I stored counts directly instead of calculating them dynamically because uploads become effectively immutable after processing.

The important part here is auditability. Analysts should always be able to trace a row back to the original uploaded file.

---

## EmissionRecord

This is the main operational table.

Different source formats eventually normalize into a common structure so the review UI can work consistently regardless of source.

Core normalized fields:

* activity type
* quantity
* unit
* activity date
* location
* scope
* review status

I tried to avoid source-specific UI logic as much as possible.

---

## Scope classification

I used a simple mapping approach:

| Source               | Scope   |
| -------------------- | ------- |
| SAP fuel/procurement | Scope 1 |
| Utility electricity  | Scope 2 |
| Corporate travel     | Scope 3 |

This is simplified compared to real ESG systems, but enough for the prototype.

---

## Unit normalization

SAP exports are inconsistent, especially with unit naming and localization.

The parser maps common unit codes into normalized values where possible.

I intentionally did not implement automatic unit conversions between systems like:

* gallons → litres
* miles → km

because I didn’t want the prototype silently transforming questionable data without analyst visibility.

Unknown units are stored and flagged instead.

---

## Source-of-truth tracking

One thing I wanted to preserve carefully was the original uploaded data.

Each emission record stores:

* which upload batch it came from
* original row number
* raw JSON snapshot of the uploaded row

That makes debugging and auditing much easier.

If an analyst edits something later, the original source data still exists unchanged.

---

## Review workflow

The review process is intentionally simple:

```text id="ycvv8x"
uploaded → pending_review
                 ├── approved
                 └── rejected

parse_error → failed
```

Suspicious records are separate from approval status.

For example:

* a suspicious record can still be approved
* or a normal record can still be rejected

I didn’t want suspicious flags automatically blocking analysts.

Approved rows are treated as locked records.

---

## Why I didn’t calculate CO2e

I intentionally skipped emissions calculations in the prototype.

Real carbon accounting depends heavily on:

* regional factors
* reporting methodology
* factor source/version
* market vs location-based calculations

I felt it was more important to build a defensible ingestion and review pipeline first instead of attaching questionable emissions numbers.

---

## AuditLog

Every analyst action writes an audit row.

Mainly:

* approve
* reject
* edit actions

The goal was to keep a simple append-only history so changes can be traced later.

I avoided making the audit structure overly complicated because this prototype only has a few workflow actions.

---

## Things this model does not handle yet

A few obvious gaps:

1. proper emissions factor management
2. schema versioning for changing CSV formats
3. partial re-processing of uploads
4. concurrent analyst conflict handling
5. advanced approval workflows

If I had more time, emissions factor versioning would probably be the next major addition because that’s where real ESG complexity starts showing up.
