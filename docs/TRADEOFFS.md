
---

# TRADEOFFS.md

## 1. No CO2e calculation

### What I skipped

I did not implement actual CO2e calculations from the activity data.

The system currently stores:

* fuel quantities
* electricity consumption
* travel distances
* hotel nights

but does not convert them into emissions values.

---

### Why

The more I looked into emissions factors, the more it became clear that this is a fairly deep problem on its own.

Electricity factors vary by:

* country
* region/grid
* reporting year

Flight emissions also depend on:

* methodology source
* travel class
* radiative forcing assumptions

Even diesel factors differ slightly across datasets.

I felt that adding a hardcoded “CO2e” number without proper factor sourcing/versioning would actually make the prototype less trustworthy from an audit perspective.

So instead of building a shallow calculation layer, I focused more on:

* ingestion
* normalization
* traceability
* analyst review workflows

which seemed closer to the core of the assignment.

---

### Impact

The dashboard currently works with native activity units:

* litres
* kWh
* km
* nights

A future version could add a dedicated emissions factor system after approval/review is complete.

---

# 2. Limited pagination and filtering

### What I skipped

The review table only supports a few basic filters:

* status
* scope
* suspicious flag
* source

I did not build:

* full-text search
* advanced date filtering
* column sorting
* optimized server-side pagination

---

### Why

The assignment timeline was short, and I prioritized getting the review workflow stable first.

For a prototype-sized dataset, loading a few thousand records into the UI is still manageable.

The existing filters cover the core analyst workflow:

* reviewing pending records
* checking suspicious rows
* approving/rejecting uploads

If this became a production system, pagination would be one of the first things to improve.

---

### Impact

Very large uploads would eventually slow down the dashboard.

The backend structure already makes pagination relatively easy to add later using DRF pagination.

---

# 3. No upload preview step

### What I skipped

Uploads are processed immediately after submission.

I did not implement:

* preview-before-confirm flows
* row-by-row live validation
* streaming upload progress

---

### Why

I wanted to keep the ingestion flow simple:

1. upload file
2. process records
3. review results

Adding a preview system would significantly increase frontend and API complexity.

For example:

* temporary uploads
* draft states
* additional endpoints
* websocket/SSE updates
* cleanup logic

For the prototype, the summary counts after upload already provide enough visibility:

* failed rows
* suspicious rows
* pending review rows

---

### Impact

Analysts only see failed/suspicious rows after ingestion completes.

Not ideal UX, but still functional and easier to reason about.

---

# Other things I intentionally left out

### Bulk approve/reject

Would require:

* multi-select UI
* batch APIs
* more careful locking logic

Skipped because single-record review already demonstrates the workflow.

---

### Email notifications

I skipped upload/review notifications because they mostly involve infrastructure setup rather than interesting product or data-model decisions.

---

### Export functionality

I didn’t build CSV/Excel export for approved records.

The assignment seemed more focused on ingestion and audit workflows than reporting/export features, so I prioritized review tooling instead.

---

## Overall

In general, I tried to avoid adding features just for the sake of feature count.

Whenever I had to choose between:

* more functionality
  or
* a cleaner ingestion/review flow

I usually picked the second option.
