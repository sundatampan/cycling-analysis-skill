"""
analyze.py
==========
Compute analytics from parsed FIT data: session summaries, HR/power zones,
peak power curves, cardiac drift, and HR recovery patterns.

Usage:
    from analyze import build_summaries
    summaries, zones = build_summaries(parsed_sessions, profile)
"""

import numpy as np


# ----------------------------------------------------------------------
# Zone definitions
# ----------------------------------------------------------------------

def compute_hr_zones(hr_max):
    """5-zone HR model (% of HR max)."""
    return {
        'Z1': (0,            0.60 * hr_max),  # Recovery
        'Z2': (0.60 * hr_max, 0.70 * hr_max),  # Endurance
        'Z3': (0.70 * hr_max, 0.80 * hr_max),  # Tempo
        'Z4': (0.80 * hr_max, 0.90 * hr_max),  # Threshold
        'Z5': (0.90 * hr_max, 999),            # VO2max
    }


def compute_power_zones(ftp):
    """7-zone Coggan power model (% of FTP)."""
    return {
        'Z1': (0,         0.55 * ftp),  # Active Recovery
        'Z2': (0.55 * ftp, 0.75 * ftp),  # Endurance
        'Z3': (0.75 * ftp, 0.90 * ftp),  # Tempo
        'Z4': (0.90 * ftp, 1.05 * ftp),  # Threshold
        'Z5': (1.05 * ftp, 1.20 * ftp),  # VO2max
        'Z6': (1.20 * ftp, 1.50 * ftp),  # Anaerobic
        'Z7': (1.50 * ftp, 99999),       # Neuromuscular
    }


# ----------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------

def _best_avg_window(values, window_s):
    """Best rolling-average power over a window in seconds."""
    if len(values) < window_s:
        return None
    arr = np.asarray(values, dtype=float)
    cumsum = np.concatenate([[0], np.cumsum(arr)])
    windows = (cumsum[window_s:] - cumsum[:-window_s]) / window_s
    return float(np.max(windows))


def _time_in_zones(values, zones):
    """Count seconds (assuming 1 Hz samples) spent in each zone."""
    if not values:
        return {z: 0 for z in zones}
    out = {z: 0 for z in zones}
    for v in values:
        for z, (lo, hi) in zones.items():
            if lo <= v < hi:
                out[z] += 1
                break
    return out


# ----------------------------------------------------------------------
# Cardiac drift & HR recovery
# ----------------------------------------------------------------------

def compute_cardiac_drift(hr_values, power_values, bands=((60, 100), (100, 150))):
    """For each power band, compare HR in first half vs second half of session.

    Returns list of dicts; empty if no power data or insufficient samples.
    """
    if not power_values or all(p is None for p in power_values):
        return []
    hr = np.array(hr_values, dtype=float)
    pwr = np.array([p if p is not None else np.nan for p in power_values], dtype=float)
    if len(hr) < 200:
        return []

    half = len(hr) // 2
    results = []
    for lo, hi in bands:
        m1 = ~np.isnan(pwr[:half]) & (pwr[:half] >= lo) & (pwr[:half] < hi)
        m2 = ~np.isnan(pwr[half:]) & (pwr[half:] >= lo) & (pwr[half:] < hi)
        if m1.sum() > 30 and m2.sum() > 30:
            results.append({
                'band': f'{lo}-{hi}W',
                'hr_first_half': float(np.mean(hr[:half][m1])),
                'hr_second_half': float(np.mean(hr[half:][m2])),
                'drift_bpm': float(np.mean(hr[half:][m2]) - np.mean(hr[:half][m1])),
            })
    return results


def compute_hr_recovery_on_coast(hr_values, power_values, min_coast_s=30):
    """Find moments when power dropped to <30W for >= min_coast_s seconds
    and measure how much HR fell in the next 30 / 60 seconds.

    Healthy 50+ y/o should drop 15-25+ bpm in 30s when load drops sharply.
    """
    if not power_values or all(p is None for p in power_values):
        return None
    hr = np.array(hr_values, dtype=float)
    pwr = np.array([p if p is not None else np.nan for p in power_values], dtype=float)
    coasting = (pwr < 30) & ~np.isnan(pwr)

    drops_30 = []
    drops_60 = []
    in_block = False
    start = 0
    for i in range(len(coasting)):
        if coasting[i] and not in_block:
            start, in_block = i, True
        elif not coasting[i] and in_block:
            if i - start >= min_coast_s:
                if start + 30 < len(hr):
                    drops_30.append(hr[start] - hr[start + 30])
                if start + 60 < len(hr):
                    drops_60.append(hr[start] - hr[start + 60])
            in_block = False

    if not drops_30:
        return None
    return {
        'coast_blocks': len(drops_30),
        'mean_drop_30s': float(np.mean(drops_30)),
        'mean_drop_60s': float(np.mean(drops_60)) if drops_60 else None,
        'worst_drop_30s': float(min(drops_30)),
    }


# ----------------------------------------------------------------------
# Per-session analysis
# ----------------------------------------------------------------------

def analyze_session(parsed, profile, hr_zones, pwr_zones, ftp):
    """Compute the full set of metrics for one parsed session."""
    s = parsed['session']
    records = parsed['records']

    # Aligned arrays — same length, one entry per record with HR
    # (skipping records without HR ensures HR analytics work; power slots are None where missing)
    hr_values = []
    power_aligned = []
    for r in records:
        if r.get('heart_rate') is None:
            continue
        hr_values.append(r['heart_rate'])
        power_aligned.append(r.get('power'))

    # Also keep an unaligned power list for power-only analytics (zones, peak curve)
    power_values = power_aligned
    has_power = any(p is not None for p in power_values)

    duration_s = s.get('total_elapsed_time', 0) or 0
    distance_m = s.get('total_distance', 0) or 0
    avg_speed_ms = s.get('avg_speed') or s.get('enhanced_avg_speed') or 0
    max_speed_ms = s.get('max_speed') or s.get('enhanced_max_speed') or 0

    out = {
        'date': parsed['date_iso'],
        'duration_min': round(duration_s / 60, 1),
        'distance_km': round(distance_m / 1000, 2),
        'avg_speed_kmh': round(avg_speed_ms * 3.6, 2),
        'max_speed_kmh': round(max_speed_ms * 3.6, 2),
        'avg_hr': s.get('avg_heart_rate'),
        'max_hr': s.get('max_heart_rate'),
        'avg_power': s.get('avg_power'),
        'max_power': s.get('max_power'),
        'np': s.get('normalized_power'),
        'tss': s.get('training_stress_score'),
        'IF': s.get('intensity_factor'),
        'training_effect': s.get('total_training_effect'),
        'anaerobic_te': s.get('total_anaerobic_training_effect'),
        'calories': s.get('total_calories'),
        'ascent_m': s.get('total_ascent'),
        'descent_m': s.get('total_descent'),
        'avg_cadence': s.get('avg_cadence'),
        'max_cadence': s.get('max_cadence'),
        'avg_temp': s.get('avg_temperature'),
        'max_temp': s.get('max_temperature'),
        'work_kj': round((s.get('total_work', 0) or 0) / 1000) if s.get('total_work') else None,
        'num_laps': len(parsed['laps']),
        'has_power': has_power,
    }

    # HR zone distribution
    if hr_values:
        out['hr_zone_seconds'] = _time_in_zones(hr_values, hr_zones)

    # Power zone distribution + peak power curve
    if has_power:
        clean_pwr = [p for p in power_values if p is not None]
        out['pwr_zone_seconds'] = _time_in_zones(clean_pwr, pwr_zones)
        out['p5s']   = round(_best_avg_window(clean_pwr, 5)    or 0)
        out['p1min'] = round(_best_avg_window(clean_pwr, 60)   or 0)
        out['p5min'] = round(_best_avg_window(clean_pwr, 300)  or 0)
        if len(clean_pwr) >= 1200:
            out['p20min'] = round(_best_avg_window(clean_pwr, 1200) or 0)
            out['ftp_estimate_session'] = round(out['p20min'] * 0.95)

    # Cardiac drift + HR recovery on coasting
    if has_power and hr_values:
        out['cardiac_drift'] = compute_cardiac_drift(hr_values, power_values)
        out['hr_recovery_coast'] = compute_hr_recovery_on_coast(hr_values, power_values)

    # Power-to-weight
    w = profile.get('weight_kg', 70)
    if out.get('avg_power'):
        out['avg_w_per_kg'] = round(out['avg_power'] / w, 2)
    if out.get('np'):
        out['np_w_per_kg'] = round(out['np'] / w, 2)

    return out


def build_summaries(parsed_sessions, profile):
    """Build all per-session summaries and resolve HR_MAX / FTP estimates.

    Returns: (summaries_dict_keyed_by_date, context_dict)
    """
    # Resolve HR_MAX
    hr_max = profile.get('hr_max')
    if hr_max is None:
        observed = []
        for p in parsed_sessions:
            mh = p['session'].get('max_heart_rate')
            if mh:
                observed.append(mh)
        if observed:
            # Use observed peak + 5 bpm buffer, but not below Tanaka estimate
            tanaka = 208 - 0.7 * profile.get('age', 40)
            hr_max = max(max(observed) + 5, round(tanaka))
        else:
            hr_max = round(208 - 0.7 * profile.get('age', 40))

    # Resolve FTP
    ftp = profile.get('ftp_watts')
    if ftp is None:
        # Estimate from 20-min best power across sessions
        ftp_estimates = []
        for p in parsed_sessions:
            recs = p['records']
            pwr = [r.get('power') for r in recs if r.get('power') is not None]
            if len(pwr) >= 1200:
                p20 = _best_avg_window(pwr, 1200)
                if p20:
                    ftp_estimates.append(p20 * 0.95)
        if ftp_estimates:
            ftp = round(max(ftp_estimates))
        else:
            ftp = 150  # safe default for amateur cyclist

    hr_zones = compute_hr_zones(hr_max)
    pwr_zones = compute_power_zones(ftp)

    summaries = {}
    for parsed in parsed_sessions:
        if parsed['date_iso'] is None:
            continue
        summaries[parsed['date_iso']] = analyze_session(parsed, profile, hr_zones, pwr_zones, ftp)

    context = {
        'hr_max': hr_max,
        'ftp': ftp,
        'hr_zones': hr_zones,
        'pwr_zones': pwr_zones,
        'weight_kg': profile.get('weight_kg', 70),
        'age': profile.get('age', 40),
    }
    return summaries, context


# ----------------------------------------------------------------------
# VO2 Max classification
# ----------------------------------------------------------------------

def classify_vo2max(vo2, age, gender='male'):
    """Cooper Institute classification."""
    # Male reference ranges
    male_table = {
        (20, 29): [25, 33, 42, 52, 60],
        (30, 39): [23, 31, 38, 48, 56],
        (40, 49): [20, 27, 35, 44, 52],
        (50, 59): [18, 25, 31, 42, 50],
        (60, 99): [16, 22, 28, 36, 44],
    }
    female_table = {
        (20, 29): [21, 28, 34, 42, 50],
        (30, 39): [19, 25, 31, 38, 45],
        (40, 49): [17, 22, 28, 35, 42],
        (50, 59): [15, 20, 25, 31, 39],
        (60, 99): [13, 17, 22, 28, 35],
    }
    table = female_table if gender.lower() == 'female' else male_table
    cutoffs = None
    for (lo, hi), c in table.items():
        if lo <= age <= hi:
            cutoffs = c
            break
    if cutoffs is None:
        cutoffs = list(table.values())[-1]
    labels = ['Buruk', 'Kurang', 'Cukup', 'Baik', 'Sangat Baik', 'Superior']
    for i, cut in enumerate(cutoffs):
        if vo2 < cut:
            return labels[i]
    return labels[-1]


if __name__ == '__main__':
    import sys, json
    print("This module is meant to be imported. For a smoke test, run run_analysis.py.")
