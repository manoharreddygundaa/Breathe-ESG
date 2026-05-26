
---

# DECISIONS.md

## Why I used CSV uploads for all three sources

I initially looked at direct integrations for SAP, utilities, and travel platforms, but for a 4-day prototype CSV uploads felt like the most realistic and practical choice.

For SAP, the “ideal” integration would probably be OData or BAPI/RFC depending on whether the client uses S/4HANA or ECC. But after reading through a few SAP integration examples, it became clear that in many companies sustainability teams don’t actually get direct SAP access. Usually someone exports a report from SAP and sends it over as an Excel or CSV file. So I decided to model the ingestion flow around that instead of building a fake API integration.

For utilities, I checked a few electricity providers and noticed APIs are inconsistent. Some providers support Green Button or other APIs, but a lot of facilities teams still work with portal exports or downloaded statements. Since the assignment focuses more on ingestion and review workflows, I standardized this source as CSV too.

For travel data, Concur and Navan both expose APIs, but implementing OAuth properly would take a decent amount of time for something that doesn’t really improve the prototype itself. Every platform already supports CSV exports, so I used that as the common format.

If I could ask the PM questions before building, I’d mainly want clarity on:

* whether clients actually expect direct SAP integrations
* whether there’s one standard travel provider or multiple
* whether utilities are mostly Indian or international providers

---

## SAP data scope I handled

SAP exports can get extremely messy and huge, so I intentionally narrowed the scope.

I focused on fuel and energy-related procurement/material movement style exports. The sample structure is loosely based on common SAP reports with fields like:

* Material
* Quantity
* Unit
* Plant
* Posting Date

I also included German-style column naming because a lot of SAP systems use localized field names.

Things I intentionally did not fully support:

* reversal postings
* complex material hierarchies
* IDoc/XML ingestion
* plant mapping tables
* currency handling

Negative quantities are currently flagged as suspicious instead of being automatically interpreted as reversals because I didn’t want to make assumptions silently.

---

## Utility data assumptions

I treated utility data as meter-level electricity consumption exports.

The system stores billing start and end dates, but I simplified reporting by using the billing start date as the activity date for normalization.

I ignored:

* tariff calculations
* peak/off-peak splits
* reactive power
* renewable energy certificates

because they weren’t necessary for demonstrating ingestion and review logic.

---

## Travel data assumptions

I handled:

* flights
* trains
* taxis/cabs
* hotels
* buses
* rental cars

One thing I noticed while checking Concur-style exports is that distance data is inconsistent. Sometimes you only get airport codes instead of actual km values.

In this prototype:

* if distance is missing for a distance-based activity, the row gets flagged as suspicious
* airport codes are lightly validated against a small static list

The airport validation is intentionally simple because the assignment seemed more focused on workflow design than building a complete aviation database.

Hotels are also simplified. Real systems would infer nights from check-in/check-out dates, but I kept the ingestion format flatter for simplicity.

---

## Normalization choices

A few normalization rules I settled on:

* try common SAP and ISO date formats first
* reject ambiguous dates instead of guessing
* normalize decimal separators where possible
* store unknown units but flag them
* use static material mappings for now

I intentionally avoided aggressive auto-correction because in emissions reporting it’s usually safer to surface questionable data to analysts instead of silently modifying it.

---

## Scope categorization

For simplicity:

* SAP fuel data → Scope 1
* utility electricity → Scope 2
* travel → Scope 3

This is static right now. I didn’t build per-record overrides because I wanted to prioritize ingestion and auditability first.

---

## Authentication

I used JWT auth mainly because it was lightweight and easy to integrate with React.

The assumption was that analyst accounts would be managed internally through Django admin, so I skipped:

* signup
* password reset
* email verification

for the prototype.

---

## Things I would improve with more time

A few obvious next steps:

* proper pagination
* bulk approve/reject actions
* editable lookup tables from admin
* better airport/material validation
* emissions factor calculations
* more detailed audit history

I also would have liked to support at least one real external API integration instead of only CSV ingestion, probably travel data first since the APIs are better documented.
