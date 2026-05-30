"""
parse_fit.py
============
Extract structured data (session, laps, time-series records) from a Garmin FIT file.

Usage (as a module):
    from parse_fit import parse_fit_file
    data = parse_fit_file('/path/to/activity.fit')

Returned structure:
    {
        'session': dict[str, value]    # one session-summary record
        'laps':    list[dict]          # per-lap summaries
        'records': list[dict]          # per-second time-series data
        'date_iso': 'YYYY-MM-DD'       # date extracted from start_time
    }
"""

from fitparse import FitFile
from datetime import datetime
import os
import re


def _clean(msg):
    """Convert a fitparse message to a plain dict, dropping None/unknown_* fields."""
    out = {}
    for d in msg:
        if d.value is None:
            continue
        if d.name.startswith('unknown'):
            continue
        out[d.name] = d.value
    return out


def parse_fit_file(path):
    """Parse a single .fit file and return a dict with session/laps/records.

    Returns None if the file can't be parsed.
    """
    if not os.path.exists(path):
        raise FileNotFoundError(path)

    # SESSION
    fit = FitFile(path)
    session = {}
    for msg in fit.get_messages('session'):
        session = _clean(msg)
        break  # only first session

    # LAPS
    fit = FitFile(path)
    laps = [_clean(msg) for msg in fit.get_messages('lap')]

    # RECORDS (time-series)
    fit = FitFile(path)
    records = []
    for msg in fit.get_messages('record'):
        rec = _clean(msg)
        if 'timestamp' in rec or 'heart_rate' in rec:
            records.append(rec)

    # Derive a date string for sorting / display
    date_iso = None
    if 'start_time' in session and isinstance(session['start_time'], datetime):
        # FIT timestamps are UTC; add a +8h heuristic for Indonesia local date.
        # Just use the UTC date for sorting consistency — display layer can adjust.
        date_iso = session['start_time'].strftime('%Y-%m-%d')
    elif records and 'timestamp' in records[0]:
        date_iso = records[0]['timestamp'].strftime('%Y-%m-%d')

    return {
        'session': session,
        'laps': laps,
        'records': records,
        'date_iso': date_iso,
    }


def _date_from_filename(filename):
    """Try to extract a date from a filename like '09-05-2026.fit' or '2026-05-09.fit'.

    Returns ISO YYYY-MM-DD or None.
    """
    base = os.path.basename(filename)
    # DD-MM-YYYY
    m = re.match(r'(\d{2})-(\d{2})-(\d{4})', base)
    if m:
        dd, mm, yyyy = m.groups()
        try:
            return datetime(int(yyyy), int(mm), int(dd)).strftime('%Y-%m-%d')
        except ValueError:
            pass
    # YYYY-MM-DD
    m = re.match(r'(\d{4})-(\d{2})-(\d{2})', base)
    if m:
        yyyy, mm, dd = m.groups()
        try:
            return datetime(int(yyyy), int(mm), int(dd)).strftime('%Y-%m-%d')
        except ValueError:
            pass
    return None


def discover_fit_files(directory):
    """List .fit files in a directory, sorted by date (from filename or content).

    Returns list of (filepath, date_iso) tuples sorted ascending by date.
    """
    if not os.path.isdir(directory):
        raise NotADirectoryError(directory)

    candidates = []
    for fn in os.listdir(directory):
        if fn.lower().endswith('.fit') and not fn.startswith('.'):
            full = os.path.join(directory, fn)
            date = _date_from_filename(fn)
            candidates.append((full, date))

    # If any are missing dates, parse them quickly to extract from content
    enriched = []
    for path, date in candidates:
        if date is None:
            try:
                data = parse_fit_file(path)
                date = data.get('date_iso') or '9999-99-99'
            except Exception:
                date = '9999-99-99'
        enriched.append((path, date))

    enriched.sort(key=lambda x: x[1])
    return enriched


if __name__ == '__main__':
    # Quick smoke test
    import sys
    if len(sys.argv) < 2:
        print("Usage: python parse_fit.py <directory_or_file>")
        sys.exit(1)
    arg = sys.argv[1]
    if os.path.isdir(arg):
        for path, date in discover_fit_files(arg):
            print(f"{date}  {path}")
    else:
        data = parse_fit_file(arg)
        print(f"Date: {data['date_iso']}")
        print(f"Session keys: {len(data['session'])}")
        print(f"Laps: {len(data['laps'])}")
        print(f"Records: {len(data['records'])}")
        if data['records']:
            print(f"Record sample keys: {list(data['records'][0].keys())}")
