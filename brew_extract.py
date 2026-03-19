"""
7BREW P&L Data Extraction Engine
Reads all period Excel files and returns a consolidated DataFrame.
"""

import openpyxl
import pandas as pd
import re
import os
import glob
from datetime import datetime

METRIC_ROWS = {
    'Gross Sales':              16,
    'Net Sales':                22,
    'COGS':                     33,
    'Gross Profit':             34,
    'Total Hourly Labor':       41,
    'Total Management':         45,
    'Total Labor':              46,
    'Total Benefits & Tax':     52,
    'Total Labor & Benefits':   53,
    'Gross Margin':             54,
    'Controllable Expense':     68,
    'Total Utilities':          74,
    'Total R&M':                80,
    'Total Fixed Expense':      100,
    'Total Occupancy':          104,
    'Total Marketing':          113,
    'Unit Level EBITDAR':       114,
    'Total Rent':               115,
    'Store Level EBITDA':       116,
    'EBITDA':                   129,
    'Preopening Expense':       130,
    'Net Income':               140,
}

SKIP_STANDS = {
    'All Stands', 'ENT Corp Office', 'Florida Corp Office',
    'All Stands & Offices', 'All Stands & Office'
}

def parse_period_label(filename):
    """Extract period label from filename like 'P1\'25' → ('P1\'25', 1, 2025)"""
    basename = os.path.basename(filename)
    m = re.search(r"P(\d+)'(\d+)", basename)
    if m:
        period_num = int(m.group(1))
        year = 2000 + int(m.group(2))
        label = f"P{period_num}'{m.group(2)}"
        return label, period_num, year
    return None, None, None

def parse_stand_name(raw):
    """Parse '000134 Lubbock, TX - 1' → (id, city, state, number, region)"""
    raw = str(raw).strip()
    m = re.match(r'^(\d+)\s+(.+),\s+([A-Z]{2})\s*-\s*(\d+)$', raw)
    if m:
        stand_id = m.group(1)
        city = m.group(2).strip()
        state = m.group(3)
        num = int(m.group(4))
        fl_states = {'FL'}
        region = 'Florida' if state in fl_states else 'ENT'
        display = f"{city}, {state} #{num}"
        return stand_id, city, state, num, region, display
    return raw, raw, '', 1, 'ENT', raw

def extract_file(filepath):
    """Extract all stand metrics from one period file. Returns list of row dicts."""
    label, period_num, year = parse_period_label(filepath)
    if label is None:
        return []

    wb = openpyxl.load_workbook(filepath, data_only=True)
    ws = wb.active

    # Get period end date
    date_cell = list(ws.iter_rows(min_row=4, max_row=4, min_col=2, max_col=2, values_only=True))[0][0]
    try:
        if isinstance(date_cell, datetime):
            period_date = date_cell
        else:
            period_date = datetime.strptime(str(date_cell), '%m/%d/%Y')
    except Exception:
        period_date = None

    # Get stand names and column positions from row 8
    row8 = list(ws.iter_rows(min_row=8, max_row=8, values_only=True))[0]
    stand_cols = {}
    for col_idx, val in enumerate(row8, 1):
        if val and str(val).strip() not in ['', ' ']:
            name = str(val).strip()
            if name not in SKIP_STANDS:
                stand_cols[col_idx] = name

    # Read all metric rows at once for efficiency
    all_row_data = {}
    for metric, row_num in METRIC_ROWS.items():
        row_vals = list(ws.iter_rows(min_row=row_num, max_row=row_num, values_only=True))[0]
        all_row_data[metric] = row_vals

    records = []
    for col_idx, stand_raw in stand_cols.items():
        stand_id, city, state, stand_num, region, display = parse_stand_name(stand_raw)
        row = {
            'period_label': label,
            'period_num': period_num,
            'year': year,
            'period_date': period_date,
            'stand_raw': stand_raw,
            'stand_id': stand_id,
            'city': city,
            'state': state,
            'stand_num': stand_num,
            'region': region,
            'display_name': display,
        }
        for metric, row_vals in all_row_data.items():
            val = row_vals[col_idx - 1]
            row[metric] = float(val) if isinstance(val, (int, float)) else 0.0
        records.append(row)

    return records

def extract_all(input_folder, file_pattern='7BREW Income Statement Side By Side PTD All*.xlsx'):
    """Extract all period files from folder, return consolidated DataFrame."""
    pattern = os.path.join(input_folder, file_pattern)
    files = sorted(glob.glob(pattern))
    if not files:
        raise FileNotFoundError(f"No files found matching: {pattern}")

    all_records = []
    for f in files:
        records = extract_file(f)
        all_records.extend(records)
        label, _, _ = parse_period_label(f)
        print(f"  Loaded {label}: {len(records)} stands")

    df = pd.DataFrame(all_records)

    # Sort chronologically
    df['sort_key'] = df['year'] * 100 + df['period_num']
    df = df.sort_values(['sort_key', 'stand_id']).reset_index(drop=True)

    return df

def assign_cohorts(df):
    """
    Assign each stand to an opening cohort based on its first appearance in the data.
    Also compute 'periods_open' (how many periods since first appearance).
    """
    min_sk = df['sort_key'].min()

    # Find first sort_key for each stand
    first_sk = df.groupby('stand_id')['sort_key'].min()

    def cohort_label(sk):
        if sk == min_sk:
            return "Legacy (Pre-Data)"
        yr = sk // 100
        pn = sk % 100
        return f"P{pn}'{str(yr)[-2:]}"

    cohort_map = {sid: cohort_label(sk) for sid, sk in first_sk.items()}
    df['cohort'] = df['stand_id'].map(cohort_map)
    df['first_sort_key'] = df['stand_id'].map(first_sk)

    # Periods open = rank of current period for this stand (1 = first period open)
    df['periods_open'] = df.groupby('stand_id')['sort_key'].rank(method='dense').astype(int)

    # Ramp flag: open fewer than 4 periods
    df['is_ramp'] = df['periods_open'] <= 4

    return df

def add_derived_metrics(df):
    """Add % of Net Sales metrics and other derived fields."""
    ns = df['Net Sales'].replace(0, float('nan'))

    df['COGS %'] = df['COGS'] / ns
    df['Labor %'] = df['Total Labor & Benefits'] / ns
    df['Hourly Labor %'] = df['Total Labor'] / ns
    df['Gross Margin %'] = df['Gross Margin'] / ns
    df['Store EBITDA %'] = df['Store Level EBITDA'] / ns
    df['EBITDA %'] = df['EBITDA'] / ns
    df['Controllable %'] = df['Controllable Expense'] / ns
    df['Rent %'] = df['Total Rent'] / ns
    df['Marketing %'] = df['Total Marketing'] / ns

    return df

def build_dataset(input_folder, file_pattern='7BREW Income Statement Side By Side PTD All*.xlsx'):
    """Full pipeline: extract → cohorts → derived metrics → return DataFrame."""
    print(f"Scanning: {input_folder}")
    df = extract_all(input_folder, file_pattern)
    df = assign_cohorts(df)
    df = add_derived_metrics(df)
    print(f"Total records: {len(df)} ({df['stand_id'].nunique()} unique stands, {df['period_label'].nunique()} periods)")
    return df
