"""
CSV parsing for SAP, utility, and travel uploads.

Each parser returns a list of dicts with two keys:
  - 'normalized': the cleaned fields ready for EmissionRecord
  - 'raw': the original row dict
  - 'flag': 'ok', 'suspicious', or 'failed'
  - 'flag_reason': explanation string if flagged

Parsers don't touch the database — that's the upload view's job.
"""

import csv
import io
from datetime import datetime, date
from decimal import Decimal, InvalidOperation


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def parse_date(raw: str) -> date | None:
    """
    Try a handful of date formats we realistically encounter.
    SAP defaults to DD.MM.YYYY. Utility portals usually do YYYY-MM-DD.
    Returns None if nothing matches.
    """
    formats = [
        '%d.%m.%Y',   # SAP default (German locale)
        '%Y-%m-%d',   # ISO 8601
        '%m/%d/%Y',   # US format, seen in some Concur exports
        '%d/%m/%Y',   # UK format
        '%Y%m%d',     # Compact SAP IDoc format
    ]
    raw = raw.strip()
    for fmt in formats:
        try:
            return datetime.strptime(raw, fmt).date()
        except ValueError:
            continue
    return None


def parse_decimal(raw: str) -> Decimal | None:
    # SAP sometimes uses commas as decimal separators
    cleaned = raw.strip().replace(',', '.')
    try:
        return Decimal(cleaned)
    except InvalidOperation:
        return None


SAP_UNIT_MAP = {
    # Volume
    'L': 'L', 'LT': 'L', 'GAL': 'L',  # GAL→L conversion handled elsewhere
    'l': 'L',
    # Weight (used for some materials)
    'KG': 'kg', 'T': 'tonne', 'TON': 'tonne',
    # Energy
    'KWH': 'kWh', 'MWH': 'MWh', 'GJ': 'GJ',
}

SAP_MATERIAL_SCOPE = {
    'DIESEL': ('scope1', 'diesel', 'L'),
    'PETROL': ('scope1', 'petrol', 'L'),
    'BENZIN': ('scope1', 'petrol', 'L'),  # German
    'NATURAL GAS': ('scope1', 'natural_gas', 'm3'),
    'ERDGAS': ('scope1', 'natural_gas', 'm3'),  # German
    'HSD': ('scope1', 'diesel', 'L'),  # High Speed Diesel, common in Indian SAP configs
    'FURNACE OIL': ('scope1', 'fuel_oil', 'L'),
}

# Unusually high thresholds — if a single row exceeds these, flag as suspicious
SAP_SUSPICIOUS_QUANTITY = {
    'L': Decimal('50000'),    # 50,000L of fuel in one posting is worth a look
    'kg': Decimal('100000'),
    'tonne': Decimal('500'),
}


def parse_sap_row(row: dict, row_index: int) -> dict:
    """
    SAP flat file export format (MM60 or similar procurement report).
    Expected columns: Material, Menge, Einheit, Plant, Posting_Date
    Menge = quantity in German. Einheit = unit.
    """
    result = {'raw': row, 'row_index': row_index}

    material = row.get('Material', '').strip().upper()
    raw_qty = row.get('Menge', '').strip()
    raw_unit = row.get('Einheit', '').strip().upper()
    plant = row.get('Plant', '').strip()
    raw_date = row.get('Posting_Date', '').strip()

    if not material or not raw_qty or not raw_date:
        result['flag'] = 'failed'
        result['flag_reason'] = f"Missing required field(s): material={material!r}, qty={raw_qty!r}, date={raw_date!r}"
        return result

    scope_info = SAP_MATERIAL_SCOPE.get(material)
    if not scope_info:
        result['flag'] = 'failed'
        result['flag_reason'] = f"Unknown material '{material}' — not in scope mapping"
        return result

    scope, activity_type, expected_unit = scope_info

    qty = parse_decimal(raw_qty)
    if qty is None:
        result['flag'] = 'failed'
        result['flag_reason'] = f"Could not parse quantity: {raw_qty!r}"
        return result

    if qty < 0:
        result['flag'] = 'suspicious'
        result['flag_reason'] = f"Negative quantity ({qty}) — could be a reversal posting, needs review"
    elif qty == 0:
        result['flag'] = 'suspicious'
        result['flag_reason'] = "Zero quantity — possibly a cancelled posting"
    else:
        result['flag'] = 'ok'
        result['flag_reason'] = ''

    # Unit normalization
    normalized_unit = SAP_UNIT_MAP.get(raw_unit, raw_unit)

    # Sanity check on quantity
    threshold = SAP_SUSPICIOUS_QUANTITY.get(normalized_unit)
    if threshold and qty > threshold and result['flag'] == 'ok':
        result['flag'] = 'suspicious'
        result['flag_reason'] = f"Unusually high quantity: {qty} {normalized_unit}"

    activity_date = parse_date(raw_date)
    if not activity_date:
        result['flag'] = 'failed'
        result['flag_reason'] = f"Could not parse date: {raw_date!r}"
        return result

    result['normalized'] = {
        'scope': scope,
        'activity_type': activity_type,
        'quantity': qty,
        'unit': normalized_unit,
        'activity_date': activity_date,
        'location': plant,
        'description': f"SAP material: {material}",
    }
    return result


# ---------------------------------------------------------------------------
# Utility electricity parser
# ---------------------------------------------------------------------------

def parse_utility_row(row: dict, row_index: int) -> dict:
    """
    Portal CSV export from utility providers.
    Expected columns: Meter_ID, Consumption_kWh, Billing_Start, Billing_End

    We use Billing_Start as the activity date. Some portals give half-months
    or misaligned billing periods — we just take the start and note it.
    """
    result = {'raw': row, 'row_index': row_index}

    meter_id = row.get('Meter_ID', '').strip()
    raw_kwh = row.get('Consumption_kWh', '').strip()
    raw_start = row.get('Billing_Start', '').strip()
    raw_end = row.get('Billing_End', '').strip()

    if not meter_id or not raw_kwh or not raw_start:
        result['flag'] = 'failed'
        result['flag_reason'] = f"Missing required field(s): meter={meter_id!r}, kwh={raw_kwh!r}, start={raw_start!r}"
        return result

    kwh = parse_decimal(raw_kwh)
    if kwh is None:
        result['flag'] = 'failed'
        result['flag_reason'] = f"Could not parse consumption: {raw_kwh!r}"
        return result

    if kwh < 0:
        result['flag'] = 'suspicious'
        result['flag_reason'] = f"Negative consumption ({kwh} kWh) — check for credit/adjustment rows"
    elif kwh > Decimal('500000'):
        result['flag'] = 'suspicious'
        result['flag_reason'] = f"Consumption {kwh} kWh is very high for a single meter — verify meter ID"
    else:
        result['flag'] = 'ok'
        result['flag_reason'] = ''

    activity_date = parse_date(raw_start)
    if not activity_date:
        result['flag'] = 'failed'
        result['flag_reason'] = f"Could not parse billing start date: {raw_start!r}"
        return result

    description = f"Billing period: {raw_start} to {raw_end}" if raw_end else f"Billing start: {raw_start}"

    result['normalized'] = {
        'scope': 'scope2',
        'activity_type': 'electricity',
        'quantity': kwh,
        'unit': 'kWh',
        'activity_date': activity_date,
        'location': meter_id,
        'description': description,
    }
    return result


# ---------------------------------------------------------------------------
# Corporate travel parser
# ---------------------------------------------------------------------------

# IATA codes we know. In a real system this would be a proper lookup table.
# We're keeping ~20 common ones for the prototype and flagging unknowns.
KNOWN_IATA = {
    'DEL', 'BOM', 'BLR', 'HYD', 'MAA', 'CCU', 'AMD', 'COK',
    'LHR', 'LGW', 'CDG', 'FRA', 'AMS', 'DXB', 'SIN', 'HKG',
    'JFK', 'LAX', 'ORD', 'SFO', 'DFW', 'MIA', 'ATL', 'SEA',
    'NRT', 'ICN', 'SYD', 'MEL',
}

TRAVEL_TYPE_SCOPE = {
    'FLIGHT': 'scope3',
    'TRAIN': 'scope3',
    'CAB': 'scope3',
    'TAXI': 'scope3',
    'HOTEL': 'scope3',
    'RENTAL CAR': 'scope3',
    'BUS': 'scope3',
}

TRAVEL_TYPE_UNIT = {
    'FLIGHT': 'route',     # We store origin-destination as the "quantity" proxy
    'TRAIN': 'km',
    'CAB': 'km',
    'TAXI': 'km',
    'HOTEL': 'night',
    'RENTAL CAR': 'day',
    'BUS': 'km',
}


def parse_travel_row(row: dict, row_index: int) -> dict:
    """
    Corporate travel platform export (Concur/Navan style).
    Expected columns: Employee, Departure, Arrival, Travel_Type, Travel_Date, Distance_km

    Distance_km is optional — platforms like Navan sometimes provide it,
    sometimes you only have airport codes. We handle both.
    """
    result = {'raw': row, 'row_index': row_index}

    employee = row.get('Employee', '').strip()
    departure = row.get('Departure', '').strip().upper()
    arrival = row.get('Arrival', '').strip().upper()
    travel_type = row.get('Travel_Type', '').strip().upper()
    raw_date = row.get('Travel_Date', '').strip()
    raw_distance = row.get('Distance_km', '').strip()

    if not travel_type or not raw_date:
        result['flag'] = 'failed'
        result['flag_reason'] = f"Missing travel_type or date"
        return result

    if travel_type not in TRAVEL_TYPE_SCOPE:
        result['flag'] = 'failed'
        result['flag_reason'] = f"Unrecognised travel type: {travel_type!r}"
        return result

    activity_date = parse_date(raw_date)
    if not activity_date:
        result['flag'] = 'failed'
        result['flag_reason'] = f"Could not parse travel date: {raw_date!r}"
        return result

    flags = []

    # Flight-specific: validate IATA codes
    if travel_type == 'FLIGHT':
        if departure not in KNOWN_IATA:
            flags.append(f"Unknown departure IATA code: {departure!r}")
        if arrival not in KNOWN_IATA:
            flags.append(f"Unknown arrival IATA code: {arrival!r}")

    unit = TRAVEL_TYPE_UNIT[travel_type]

    if unit in ('km', 'route') and raw_distance:
        qty = parse_decimal(raw_distance)
        if qty is None:
            flags.append(f"Could not parse distance: {raw_distance!r}")
            qty = Decimal('0')
        elif qty < 0:
            flags.append(f"Negative distance: {qty}")
    elif travel_type == 'HOTEL':
        # For hotels, Departure is check-in city, Arrival isn't meaningful
        qty = Decimal('1')  # 1 night — better than nothing, flag for review
        flags.append("Hotel nights not provided — defaulting to 1, please verify")
    elif travel_type == 'RENTAL CAR':
        qty = Decimal('1')
        flags.append("Rental car days not provided — defaulting to 1, please verify")
    else:
        # No distance provided for a km-based type
        qty = Decimal('0')
        flags.append(f"No distance provided for {travel_type} — quantity set to 0")

    if flags:
        result['flag'] = 'suspicious'
        result['flag_reason'] = '; '.join(flags)
    else:
        result['flag'] = 'ok'
        result['flag_reason'] = ''

    route = f"{departure}→{arrival}" if departure and arrival else departure or arrival or 'unknown'
    description = f"{employee} | {travel_type}" if employee else travel_type

    result['normalized'] = {
        'scope': TRAVEL_TYPE_SCOPE[travel_type],
        'activity_type': travel_type.lower().replace(' ', '_'),
        'quantity': qty,
        'unit': unit,
        'activity_date': activity_date,
        'location': route,
        'description': description,
    }
    return result


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

PARSER_MAP = {
    'sap_fuel': parse_sap_row,
    'utility': parse_utility_row,
    'travel': parse_travel_row,
}


def parse_csv(file_obj, source_type: str) -> list[dict]:
    """
    Read CSV from file-like object, run each row through the appropriate parser.
    Returns list of result dicts (normalized + raw + flag).
    """
    parser = PARSER_MAP.get(source_type)
    if not parser:
        raise ValueError(f"Unknown source_type: {source_type!r}")

    content = file_obj.read()
    if isinstance(content, bytes):
        content = content.decode('utf-8', errors='replace')

    reader = csv.DictReader(io.StringIO(content))
    results = []
    for i, row in enumerate(reader, start=1):
        result = parser(row, row_index=i)
        results.append(result)

    return results
