=
---

# SOURCES.md

## SAP Fuel & Procurement

### What I looked at

I spent some time looking through common SAP export formats and reports used for procurement/material movement data.

The main ones I came across were:

* MB51 (material document list)
* ME2M (purchase orders by material)
* finance exports like FBL3N/FAGLL03
* IDoc-based integrations

For this prototype I used an MB51-style export because it seemed closest to what a sustainability or operations team would realistically send over manually.

A lot of SAP screenshots/examples online also showed German field names, so I used examples like:

* `Menge`
* `Einheit`
* `Buchungsdatum`

instead of only English column names.

---

### What I simplified

Real SAP exports are much messier than the prototype.

I intentionally reduced the structure down to a smaller set of fields:

* material
* quantity
* unit
* plant
* posting date

I also hardcoded some sample material mappings like:

* DIESEL
* HSD
* ERDGAS

In reality those codes vary heavily between clients.

Plant codes are stored directly as values like `HYD01` or `BOM02`. A real deployment would probably need:

* location mapping
* ownership metadata
* regional information

I also decided not to automatically handle reversal postings. Negative quantities are flagged as suspicious instead.

---

### What would probably fail in production

A few obvious weaknesses:

* localized SAP exports with different column names
* heavily customized layouts
* S/4HANA vs ECC differences
* client-specific material codes
* Excel exports instead of CSV

The parser is intentionally opinionated because this is still a prototype.

---

# Utility Electricity

### What I looked at

I checked how utilities usually expose electricity consumption data.

What I found:

* CSV/Excel portal downloads are very common
* PDF bills are also common
* APIs are inconsistent, especially in India
* Green Button exists but is mostly US-focused

Because of that, I treated utility ingestion as a CSV upload problem instead of an API integration problem.

The sample format uses fields like:

* meter ID
* billing period
* consumption in kWh

which matches a lot of portal export examples I found.

---

### What I simplified

I ignored:

* tariff calculations
* reactive power
* peak/off-peak rates
* demand charges

since the prototype focuses more on ingestion and analyst review workflows.

Billing periods also don’t align neatly with calendar months in real utility systems, so I just used the billing start date as the activity date.

---

### What would break in production

A few realistic issues:

* `.xlsx` instead of CSV
* utilities reporting MWh instead of kWh
* multiple rows for peak/off-peak periods
* billing correction entries with negative values

Right now suspicious values are surfaced to analysts rather than auto-corrected.

---

# Corporate Travel

### What I looked at

I mainly researched:

* SAP Concur
* Navan
* Happay
* ITILITE

Concur looked the most common in large enterprises, especially for structured travel exports.

The exports I found usually included:

* origin/destination
* travel type
* travel dates
* sometimes distance
* sometimes booking class

One thing I noticed quickly is that distance information is inconsistent. Some exports provide it directly, others only provide airport or city codes.

---

### What I simplified

The prototype combines:

* flights
* hotels
* cabs
* trains
* buses

into one ingestion flow.

In reality those may come from different export sections or even different systems.

I also simplified location handling:

* flights ideally use IATA codes
* trains/cabs usually use city names

but the prototype stores both similarly.

Hotel handling is also simplified. Real systems would derive nights from check-in/check-out dates.

---

### What would break in production

Main issues:

* missing distance values
* miles vs kilometres
* incomplete airport validation
* multi-leg trips
* inconsistent naming conventions

The IATA lookup is intentionally tiny for the prototype. A real deployment would need a full airport database.

I also skipped travel class handling even though business/economy emissions differ significantly.

---

## Overall takeaway

The biggest thing I noticed while researching these sources is that the hard part is not emissions calculation itself.

The hard part is:

* inconsistent exports
* missing fields
* localization
* messy units
* review workflows
* making ingestion traceable enough for audits

That’s why the prototype focuses much more on normalization and analyst review than on calculating CO2e directly.
