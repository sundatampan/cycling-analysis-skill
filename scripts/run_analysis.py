"""
run_analysis.py
===============
End-to-end orchestrator: reads a JSON config, parses FIT files, analyzes,
generates charts, and assembles the final PDF report.

Usage:
    python run_analysis.py --config /path/to/config.json

Config schema:
    {
      "name": "...",
      "age": int,
      "weight_kg": int,
      "height_cm": int (optional),
      "gender": "male" or "female",
      "vo2max_cycling": float (optional),
      "vo2max_running": float (optional),
      "ftp_watts": int or null,
      "hr_max": int or null,
      "language": "id" or "en",
      "medical_notes": str or null,
      "fit_files_dir": "/path/to/fit/files",
      "output_pdf": "/path/to/output.pdf"
    }
"""

import argparse
import json
import os
import sys
import tempfile

# Make sibling modules importable
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from parse_fit import parse_fit_file, discover_fit_files
from analyze import build_summaries
from make_charts import generate_all_charts
from make_pdf import build_pdf


def main():
    parser = argparse.ArgumentParser(description="Generate cycling analysis PDF from FIT files")
    parser.add_argument('--config', required=True, help='Path to JSON config file')
    args = parser.parse_args()

    # Load config
    with open(args.config) as f:
        cfg = json.load(f)

    # Required fields
    required = ['name', 'age', 'weight_kg', 'fit_files_dir', 'output_pdf']
    missing = [k for k in required if not cfg.get(k)]
    if missing:
        print(f"ERROR: missing required config fields: {missing}", file=sys.stderr)
        sys.exit(1)

    # Defaults
    cfg.setdefault('language', 'id')
    cfg.setdefault('gender', 'male')
    cfg.setdefault('height_cm', 170)
    cfg.setdefault('ftp_watts', None)
    cfg.setdefault('hr_max', None)
    cfg.setdefault('medical_notes', None)
    cfg.setdefault('vo2max_cycling', None)
    cfg.setdefault('vo2max_running', None)

    print(f"=== Cycling Analysis: {cfg['name']} ===")
    print(f"Language: {cfg['language']}")

    # Discover and parse FIT files
    fit_files = discover_fit_files(cfg['fit_files_dir'])
    if not fit_files:
        print(f"ERROR: no .fit files found in {cfg['fit_files_dir']}", file=sys.stderr)
        sys.exit(1)
    print(f"\nFound {len(fit_files)} FIT files:")
    for path, date in fit_files:
        print(f"  {date}  {os.path.basename(path)}")

    parsed = []
    for path, _ in fit_files:
        try:
            data = parse_fit_file(path)
            if data['session']:
                parsed.append(data)
        except Exception as e:
            print(f"  WARN: failed to parse {path}: {e}", file=sys.stderr)

    if not parsed:
        print("ERROR: no parsable sessions", file=sys.stderr)
        sys.exit(1)

    # Build profile
    profile = {
        'name': cfg['name'],
        'age': cfg['age'],
        'weight_kg': cfg['weight_kg'],
        'height_cm': cfg['height_cm'],
        'gender': cfg['gender'],
        'vo2max_cycling': cfg['vo2max_cycling'],
        'vo2max_running': cfg['vo2max_running'],
        'ftp_watts': cfg['ftp_watts'],
        'hr_max': cfg['hr_max'],
        'medical_notes': cfg['medical_notes'],
    }

    # Analytics
    print("\nComputing analytics...")
    summaries, context = build_summaries(parsed, profile)
    print(f"  HR Max (used): {context['hr_max']} bpm")
    print(f"  FTP (used): {context['ftp']} W ({context['ftp']/profile['weight_kg']:.2f} W/kg)")

    # Print per-session summary
    print("\nPer-session summary:")
    print(f"  {'Date':<12} {'Dist':>7} {'Dur':>6} {'AvgHR':>6} {'AvgP':>6} {'NP':>5} {'TSS':>6}")
    for d in sorted(summaries.keys()):
        s = summaries[d]
        print(f"  {d:<12} {s['distance_km']:>6.1f}k {int(s['duration_min']):>5}m "
              f"{(s.get('avg_hr') or 0):>5} {(s.get('avg_power') or 0):>5} "
              f"{(s.get('np') or 0):>4} {(s.get('tss') or 0):>5.1f}")

    # Generate charts in a temp directory
    print("\nGenerating charts...")
    charts_dir = tempfile.mkdtemp(prefix='cycling_charts_')
    charts = generate_all_charts(summaries, context, parsed, charts_dir, lang=cfg['language'])
    n_charts = sum(1 for v in charts.values() if v and os.path.exists(v))
    print(f"  {n_charts} charts created in {charts_dir}")

    # Build PDF
    print(f"\nBuilding PDF: {cfg['output_pdf']}")
    os.makedirs(os.path.dirname(cfg['output_pdf']), exist_ok=True)
    build_pdf(summaries, context, charts, profile, cfg['output_pdf'], lang=cfg['language'])
    size = os.path.getsize(cfg['output_pdf'])
    print(f"  Done. {size:,} bytes")

    # Surface cardiac alerts if any
    alerts = []
    for d in sorted(summaries.keys()):
        s = summaries[d]
        for drift in (s.get('cardiac_drift') or []):
            if abs(drift.get('drift_bpm', 0)) > 10:
                alerts.append(f"  {d}: cardiac drift {drift['drift_bpm']:+.1f} bpm at {drift['band']}")
        rec = s.get('hr_recovery_coast') or {}
        if rec and rec.get('mean_drop_30s') is not None and rec['mean_drop_30s'] < 5:
            alerts.append(f"  {d}: slow HR recovery on coasting ({rec['mean_drop_30s']:+.1f} bpm/30s avg)")
    if alerts:
        print("\n⚠ Cardiac findings worth highlighting to the user:")
        for a in alerts:
            print(a)

    print(f"\n✓ Report ready: {cfg['output_pdf']}")
    return cfg['output_pdf']


if __name__ == '__main__':
    main()
