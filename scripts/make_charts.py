"""
make_charts.py
==============
Generate matplotlib charts from per-session summaries. All chart functions
write PNG files to a charts directory and accept a `lang` parameter for
'id' (Bahasa Indonesia) or 'en' (English) labels.

Usage:
    from make_charts import generate_all_charts
    chart_paths = generate_all_charts(summaries, context, parsed_sessions,
                                       charts_dir, lang='id')
"""

import os
import numpy as np
import matplotlib
matplotlib.use('Agg')  # headless
import matplotlib.pyplot as plt

plt.rcParams['font.family'] = 'DejaVu Sans'
plt.rcParams['axes.grid'] = True
plt.rcParams['grid.alpha'] = 0.3

COLORS = {
    'primary':   '#1f77b4',
    'secondary': '#ff7f0e',
    'success':   '#2ca02c',
    'danger':    '#d62728',
    'warning':   '#ffbb33',
    'info':      '#17a2b8',
    'purple':    '#9467bd',
}

ZONE_HR_COLORS = ['#4caf50', '#8bc34a', '#ffc107', '#ff9800', '#f44336']
ZONE_PWR_COLORS = ['#2196f3', '#4caf50', '#cddc39', '#ffeb3b', '#ff9800', '#f44336', '#9c27b0']

# ----------------------------------------------------------------------
# i18n labels
# ----------------------------------------------------------------------

LABELS = {
    'id': {
        'date': 'Tanggal Latihan',
        'distance_km': 'Jarak (km)',
        'duration_min': 'Durasi (menit)',
        'title_dist_dur': 'Jarak Tempuh & Durasi per Sesi Latihan',
        'avg': 'Rata-rata',
        'max': 'Maksimum',
        'hr_bpm': 'Detak Jantung (bpm)',
        'hr_max_est': 'HR Maks estimasi',
        'title_hr': 'Detak Jantung Rata-rata & Maksimum per Sesi',
        'power_w': 'Power (Watt)',
        'avg_power': 'Rata-rata Power',
        'norm_power': 'Normalized Power (NP)',
        'max_power': 'Maksimum Power',
        'title_power': 'Output Power per Sesi (Avg / NP / Max)',
        'tss_title': 'Training Stress Score (TSS)',
        'light': 'Ringan (<50)',
        'medium': 'Sedang (50-100)',
        'heavy': 'Berat (>100)',
        'te_title': 'Training Effect (Aerobic & Anaerobic)',
        'aerobic_te': 'Aerobic TE',
        'anaerobic_te': 'Anaerobic TE',
        'pct_time_hr_zone': '% Waktu di Zona HR',
        'title_hr_zones': 'Distribusi Waktu di Zona Detak Jantung',
        'pct_time_pwr_zone': '% Waktu di Zona Power',
        'title_pwr_zones': 'Distribusi Waktu di Zona Power (FTP = {ftp} W)',
        'duration_label': 'Durasi Puncak',
        'sec': 'detik',
        'min': 'menit',
        'title_power_curve': 'Kurva Power Puncak per Durasi',
        'speed_kmh': 'Kecepatan (km/jam)',
        'title_speed': 'Kecepatan Rata-rata & Maksimum',
        'cadence_rpm': 'Cadence (rpm)',
        'title_cadence': 'Cadence Rata-rata & Maksimum',
        'optimal_cadence': 'Zona optimal (85-95)',
        'time_min': 'Waktu (menit)',
        'hr_label_short': 'HR (bpm)',
        'avg_30s': 'Avg 30 dtk',
        'distance_km_axis': 'Jarak (km)',
        'altitude_m': 'Elevasi (m)',
        'no_hr_data': 'Tidak ada data HR',
        'no_elev_data': 'Tidak ada data elevasi',
        'hr_trace': 'Profil HR',
        'pwr_trace': 'Profil Power',
        'elev_profile': 'Profil Elevasi',
        'ascent': 'Asc',
    },
    'en': {
        'date': 'Training Date',
        'distance_km': 'Distance (km)',
        'duration_min': 'Duration (min)',
        'title_dist_dur': 'Distance & Duration per Training Session',
        'avg': 'Average',
        'max': 'Maximum',
        'hr_bpm': 'Heart Rate (bpm)',
        'hr_max_est': 'Estimated HR Max',
        'title_hr': 'Average & Max Heart Rate per Session',
        'power_w': 'Power (W)',
        'avg_power': 'Avg Power',
        'norm_power': 'Normalized Power (NP)',
        'max_power': 'Max Power',
        'title_power': 'Power Output per Session (Avg / NP / Max)',
        'tss_title': 'Training Stress Score (TSS)',
        'light': 'Light (<50)',
        'medium': 'Moderate (50-100)',
        'heavy': 'Heavy (>100)',
        'te_title': 'Training Effect (Aerobic & Anaerobic)',
        'aerobic_te': 'Aerobic TE',
        'anaerobic_te': 'Anaerobic TE',
        'pct_time_hr_zone': '% Time in HR Zone',
        'title_hr_zones': 'Time Distribution by Heart Rate Zone',
        'pct_time_pwr_zone': '% Time in Power Zone',
        'title_pwr_zones': 'Time Distribution by Power Zone (FTP = {ftp} W)',
        'duration_label': 'Peak Duration',
        'sec': 'sec',
        'min': 'min',
        'title_power_curve': 'Peak Power Curve by Duration',
        'speed_kmh': 'Speed (km/h)',
        'title_speed': 'Average & Max Speed',
        'cadence_rpm': 'Cadence (rpm)',
        'title_cadence': 'Average & Max Cadence',
        'optimal_cadence': 'Optimal zone (85-95)',
        'time_min': 'Time (min)',
        'hr_label_short': 'HR (bpm)',
        'avg_30s': '30-sec avg',
        'distance_km_axis': 'Distance (km)',
        'altitude_m': 'Altitude (m)',
        'no_hr_data': 'No HR data',
        'no_elev_data': 'No elevation data',
        'hr_trace': 'HR Trace',
        'pwr_trace': 'Power Trace',
        'elev_profile': 'Elevation Profile',
        'ascent': 'Asc',
    },
}


def _L(lang):
    return LABELS.get(lang, LABELS['id'])


def _date_label(date_iso):
    return date_iso[8:10] + '/' + date_iso[5:7]


# ----------------------------------------------------------------------
# Individual chart generators
# ----------------------------------------------------------------------

def chart_distance_duration(summaries, charts_dir, lang='id'):
    L = _L(lang)
    dates = sorted(summaries.keys())
    distances = [summaries[d]['distance_km'] for d in dates]
    durations = [summaries[d]['duration_min'] for d in dates]
    labels = [_date_label(d) for d in dates]

    fig, ax1 = plt.subplots(figsize=(9, 4.5))
    x = np.arange(len(dates))
    w = 0.35
    b1 = ax1.bar(x - w/2, distances, w, label=L['distance_km'], color=COLORS['primary'])
    ax1.set_xlabel(L['date'])
    ax1.set_ylabel(L['distance_km'], color=COLORS['primary'])
    ax1.tick_params(axis='y', labelcolor=COLORS['primary'])
    ax1.set_xticks(x)
    ax1.set_xticklabels(labels)
    for b, v in zip(b1, distances):
        ax1.text(b.get_x()+b.get_width()/2, v+0.5, f'{v:.1f}', ha='center', fontsize=9, color=COLORS['primary'])

    ax2 = ax1.twinx()
    b2 = ax2.bar(x + w/2, durations, w, label=L['duration_min'], color=COLORS['secondary'])
    ax2.set_ylabel(L['duration_min'], color=COLORS['secondary'])
    ax2.tick_params(axis='y', labelcolor=COLORS['secondary'])
    ax2.grid(False)
    for b, v in zip(b2, durations):
        ax2.text(b.get_x()+b.get_width()/2, v+1, f'{v:.0f}', ha='center', fontsize=9, color=COLORS['secondary'])

    plt.title(L['title_dist_dur'], fontweight='bold')
    fig.tight_layout()
    out = os.path.join(charts_dir, '01_distance_duration.png')
    plt.savefig(out, dpi=140, bbox_inches='tight')
    plt.close()
    return out


def chart_heartrate(summaries, context, charts_dir, lang='id'):
    L = _L(lang)
    dates = sorted(summaries.keys())
    labels = [_date_label(d) for d in dates]
    avg_hrs = [summaries[d]['avg_hr'] or 0 for d in dates]
    max_hrs = [summaries[d]['max_hr'] or 0 for d in dates]
    hr_max = context['hr_max']

    fig, ax = plt.subplots(figsize=(9, 4.5))
    x = np.arange(len(dates))
    w = 0.35
    b1 = ax.bar(x - w/2, avg_hrs, w, label=f"{L['avg']} HR", color=COLORS['info'])
    b2 = ax.bar(x + w/2, max_hrs, w, label=f"{L['max']} HR", color=COLORS['danger'])
    ax.axhline(hr_max, color='gray', linestyle='--', alpha=0.5, label=f"{L['hr_max_est']} ({hr_max})")
    ax.set_xlabel(L['date'])
    ax.set_ylabel(L['hr_bpm'])
    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    ax.set_title(L['title_hr'], fontweight='bold')
    ax.legend(loc='lower right')
    for b, v in zip(b1, avg_hrs):
        if v: ax.text(b.get_x()+b.get_width()/2, v+1, f'{v}', ha='center', fontsize=9)
    for b, v in zip(b2, max_hrs):
        if v: ax.text(b.get_x()+b.get_width()/2, v+1, f'{v}', ha='center', fontsize=9)
    ax.set_ylim(0, hr_max + 20)
    plt.tight_layout()
    out = os.path.join(charts_dir, '02_heartrate.png')
    plt.savefig(out, dpi=140, bbox_inches='tight')
    plt.close()
    return out


def chart_power(summaries, context, charts_dir, lang='id'):
    L = _L(lang)
    dates = sorted(summaries.keys())
    pdates = [d for d in dates if summaries[d].get('avg_power') is not None]
    if not pdates:
        return None
    labels = [_date_label(d) for d in pdates]
    pavg = [summaries[d]['avg_power'] for d in pdates]
    pnp  = [summaries[d].get('np') or 0 for d in pdates]
    pmax = [summaries[d]['max_power'] for d in pdates]
    ftp = context['ftp']

    fig, ax = plt.subplots(figsize=(9, 4.5))
    x = np.arange(len(pdates))
    w = 0.27
    b1 = ax.bar(x - w, pavg, w, label=L['avg_power'], color=COLORS['primary'])
    b2 = ax.bar(x,     pnp,  w, label=L['norm_power'], color=COLORS['purple'])
    b3 = ax.bar(x + w, pmax, w, label=L['max_power'], color=COLORS['danger'])
    ax.axhline(ftp, color='green', linestyle='--', alpha=0.6, label=f'FTP ({ftp} W)')
    ax.set_xlabel(L['date'])
    ax.set_ylabel(L['power_w'])
    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    ax.set_title(L['title_power'], fontweight='bold')
    ax.legend(loc='upper left')
    for bars, vals in [(b1, pavg), (b2, pnp), (b3, pmax)]:
        for b, v in zip(bars, vals):
            if v: ax.text(b.get_x()+b.get_width()/2, v+5, f'{v}', ha='center', fontsize=8)
    plt.tight_layout()
    out = os.path.join(charts_dir, '03_power.png')
    plt.savefig(out, dpi=140, bbox_inches='tight')
    plt.close()
    return out


def chart_tss_te(summaries, charts_dir, lang='id'):
    L = _L(lang)
    dates = sorted(summaries.keys())
    labels = [_date_label(d) for d in dates]
    tss = [summaries[d].get('tss') or 0 for d in dates]
    te  = [summaries[d].get('training_effect') or 0 for d in dates]
    ate = [summaries[d].get('anaerobic_te') or 0 for d in dates]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 4.5))
    x = np.arange(len(dates))
    b = ax1.bar(x, tss, color=COLORS['warning'])
    ax1.set_xticks(x); ax1.set_xticklabels(labels)
    ax1.set_ylabel('TSS')
    ax1.set_title(L['tss_title'], fontweight='bold')
    for bar, v in zip(b, tss):
        if v: ax1.text(bar.get_x()+bar.get_width()/2, v+1, f'{v:.1f}', ha='center', fontsize=9)
    ax1.axhspan(0, 50,   alpha=0.1, color='green',  label=L['light'])
    ax1.axhspan(50, 100, alpha=0.1, color='orange', label=L['medium'])
    ax1.axhspan(100, 200, alpha=0.1, color='red',   label=L['heavy'])
    ax1.legend(loc='upper left', fontsize=8)

    w = 0.35
    ba = ax2.bar(x - w/2, te,  w, label=L['aerobic_te'],   color=COLORS['success'])
    bb = ax2.bar(x + w/2, ate, w, label=L['anaerobic_te'], color=COLORS['danger'])
    ax2.set_xticks(x); ax2.set_xticklabels(labels)
    ax2.set_ylabel('Training Effect (0-5)')
    ax2.set_ylim(0, 5.5)
    ax2.set_title(L['te_title'], fontweight='bold')
    ax2.legend(loc='upper left')
    for bars, vals in [(ba, te), (bb, ate)]:
        for bar, v in zip(bars, vals):
            if v: ax2.text(bar.get_x()+bar.get_width()/2, v+0.05, f'{v:.1f}', ha='center', fontsize=8)
    plt.tight_layout()
    out = os.path.join(charts_dir, '04_tss_te.png')
    plt.savefig(out, dpi=140, bbox_inches='tight')
    plt.close()
    return out


def chart_hr_zones(summaries, charts_dir, lang='id'):
    L = _L(lang)
    dates = sorted(summaries.keys())
    labels = [_date_label(d) for d in dates]
    zone_names = ['Z1', 'Z2', 'Z3', 'Z4', 'Z5']
    descs = ['Z1 (Recovery)', 'Z2 (Endurance)', 'Z3 (Tempo)', 'Z4 (Threshold)', 'Z5 (VO2max)']

    zone_data = {z: [] for z in zone_names}
    for d in dates:
        s = summaries[d]
        zs = s.get('hr_zone_seconds', {z: 0 for z in zone_names})
        total = sum(zs.values()) or 1
        for z in zone_names:
            zone_data[z].append(zs.get(z, 0) / total * 100)

    fig, ax = plt.subplots(figsize=(9, 4.5))
    x = np.arange(len(dates))
    bottom = np.zeros(len(dates))
    for i, z in enumerate(zone_names):
        vals = zone_data[z]
        ax.bar(x, vals, bottom=bottom, label=descs[i], color=ZONE_HR_COLORS[i])
        for j, v in enumerate(vals):
            if v > 4:
                ax.text(x[j], bottom[j] + v/2, f'{v:.0f}%', ha='center', va='center',
                        fontsize=8, fontweight='bold', color='white')
        bottom += np.array(vals)

    ax.set_xticks(x); ax.set_xticklabels(labels)
    ax.set_ylabel(L['pct_time_hr_zone'])
    ax.set_ylim(0, 105)
    ax.set_title(L['title_hr_zones'], fontweight='bold')
    ax.legend(loc='center left', bbox_to_anchor=(1.01, 0.5), fontsize=9)
    ax.grid(False)
    plt.tight_layout()
    out = os.path.join(charts_dir, '05_hr_zones.png')
    plt.savefig(out, dpi=140, bbox_inches='tight')
    plt.close()
    return out


def chart_power_zones(summaries, context, charts_dir, lang='id'):
    L = _L(lang)
    dates = sorted(summaries.keys())
    pdates = [d for d in dates if summaries[d].get('pwr_zone_seconds')]
    if not pdates:
        return None
    labels = [_date_label(d) for d in pdates]
    zone_names = ['Z1', 'Z2', 'Z3', 'Z4', 'Z5', 'Z6', 'Z7']
    descs = ['Z1 (Active Recovery)', 'Z2 (Endurance)', 'Z3 (Tempo)', 'Z4 (Threshold)',
             'Z5 (VO2max)', 'Z6 (Anaerobic)', 'Z7 (Neuromuscular)']

    zone_data = {z: [] for z in zone_names}
    for d in pdates:
        zs = summaries[d]['pwr_zone_seconds']
        total = sum(zs.values()) or 1
        for z in zone_names:
            zone_data[z].append(zs.get(z, 0) / total * 100)

    fig, ax = plt.subplots(figsize=(9, 4.5))
    x = np.arange(len(pdates))
    bottom = np.zeros(len(pdates))
    for i, z in enumerate(zone_names):
        vals = zone_data[z]
        ax.bar(x, vals, bottom=bottom, label=descs[i], color=ZONE_PWR_COLORS[i])
        for j, v in enumerate(vals):
            if v > 4:
                ax.text(x[j], bottom[j] + v/2, f'{v:.0f}%', ha='center', va='center',
                        fontsize=8, fontweight='bold', color='white')
        bottom += np.array(vals)

    ax.set_xticks(x); ax.set_xticklabels(labels)
    ax.set_ylabel(L['pct_time_pwr_zone'])
    ax.set_ylim(0, 105)
    ax.set_title(L['title_pwr_zones'].format(ftp=context['ftp']), fontweight='bold')
    ax.legend(loc='center left', bbox_to_anchor=(1.01, 0.5), fontsize=8)
    ax.grid(False)
    plt.tight_layout()
    out = os.path.join(charts_dir, '06_pwr_zones.png')
    plt.savefig(out, dpi=140, bbox_inches='tight')
    plt.close()
    return out


def chart_power_curve(summaries, charts_dir, lang='id'):
    L = _L(lang)
    pdates = [d for d in sorted(summaries.keys())
              if summaries[d].get('p5s') is not None]
    if not pdates:
        return None
    labels = [_date_label(d) for d in pdates]
    keys = ['p5s', 'p1min', 'p5min', 'p20min']
    duration_labels = [f"5 {L['sec']}", f"1 {L['min']}", f"5 {L['min']}", f"20 {L['min']}"]

    fig, ax = plt.subplots(figsize=(9, 4.5))
    x = np.arange(len(keys))
    n = len(pdates)
    bw = 0.8 / max(n, 1)
    cmap = plt.cm.viridis(np.linspace(0.15, 0.85, n))
    for i, d in enumerate(pdates):
        vals = [summaries[d].get(k) or 0 for k in keys]
        offset = (i - (n-1)/2) * bw
        bars = ax.bar(x + offset, vals, bw, label=labels[i], color=cmap[i])
        for b, v in zip(bars, vals):
            if v: ax.text(b.get_x()+b.get_width()/2, v+5, f'{v}', ha='center', fontsize=7)

    ax.set_xticks(x)
    ax.set_xticklabels(duration_labels)
    ax.set_ylabel(L['power_w'])
    ax.set_xlabel(L['duration_label'])
    ax.set_title(L['title_power_curve'], fontweight='bold')
    ax.legend(title=L['date'])
    plt.tight_layout()
    out = os.path.join(charts_dir, '07_power_curve.png')
    plt.savefig(out, dpi=140, bbox_inches='tight')
    plt.close()
    return out


def chart_speed_cadence(summaries, charts_dir, lang='id'):
    L = _L(lang)
    dates = sorted(summaries.keys())
    labels = [_date_label(d) for d in dates]
    avg_spd = [summaries[d]['avg_speed_kmh'] for d in dates]
    max_spd = [summaries[d]['max_speed_kmh'] for d in dates]
    cad_avg = [summaries[d].get('avg_cadence') or 0 for d in dates]
    cad_max = [summaries[d].get('max_cadence') or 0 for d in dates]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 4.5))
    x = np.arange(len(dates))
    w = 0.35
    b1 = ax1.bar(x - w/2, avg_spd, w, label=L['avg'], color=COLORS['primary'])
    b2 = ax1.bar(x + w/2, max_spd, w, label=L['max'], color=COLORS['danger'])
    ax1.set_xticks(x); ax1.set_xticklabels(labels)
    ax1.set_ylabel(L['speed_kmh'])
    ax1.set_title(L['title_speed'], fontweight='bold')
    ax1.legend()
    for bars, vals in [(b1, avg_spd), (b2, max_spd)]:
        for b, v in zip(bars, vals):
            if v: ax1.text(b.get_x()+b.get_width()/2, v+0.5, f'{v:.1f}', ha='center', fontsize=9)

    b1 = ax2.bar(x - w/2, cad_avg, w, label=L['avg'], color=COLORS['success'])
    b2 = ax2.bar(x + w/2, cad_max, w, label=L['max'], color=COLORS['warning'])
    ax2.set_xticks(x); ax2.set_xticklabels(labels)
    ax2.set_ylabel(L['cadence_rpm'])
    ax2.set_title(L['title_cadence'], fontweight='bold')
    ax2.axhspan(85, 95, alpha=0.15, color='green', label=L['optimal_cadence'])
    ax2.legend()
    for bars, vals in [(b1, cad_avg), (b2, cad_max)]:
        for b, v in zip(bars, vals):
            if v: ax2.text(b.get_x()+b.get_width()/2, v+1, f'{v}', ha='center', fontsize=9)
    plt.tight_layout()
    out = os.path.join(charts_dir, '08_speed_cadence.png')
    plt.savefig(out, dpi=140, bbox_inches='tight')
    plt.close()
    return out


def chart_hr_traces(parsed_sessions, summaries, context, charts_dir, lang='id'):
    L = _L(lang)
    dates = sorted(summaries.keys())
    by_date = {p['date_iso']: p for p in parsed_sessions if p['date_iso']}
    hr_max = context['hr_max']

    n = len(dates)
    cols = 2 if n > 1 else 1
    rows = (n + cols - 1) // cols
    fig, axes = plt.subplots(rows, cols, figsize=(11, 3.5*rows))
    if n == 1:
        axes = [axes]
    else:
        axes = np.array(axes).flatten()
    for idx, d in enumerate(dates):
        ax = axes[idx]
        recs = by_date[d]['records']
        hrs = [r['heart_rate'] for r in recs if 'heart_rate' in r]
        if not hrs:
            ax.set_title(f"{_date_label(d)} - {L['no_hr_data']}", fontsize=10)
            continue
        t = np.arange(len(hrs)) / 60.0
        ax.plot(t, hrs, color=COLORS['danger'], linewidth=0.7)
        ax.axhspan(0,             0.60*hr_max, alpha=0.07, color='green')
        ax.axhspan(0.60*hr_max,   0.70*hr_max, alpha=0.07, color='lightgreen')
        ax.axhspan(0.70*hr_max,   0.80*hr_max, alpha=0.07, color='yellow')
        ax.axhspan(0.80*hr_max,   0.90*hr_max, alpha=0.07, color='orange')
        ax.axhspan(0.90*hr_max,   hr_max+30,   alpha=0.07, color='red')
        ax.set_title(f"{_date_label(d)} — {L['hr_trace']}", fontsize=10, fontweight='bold')
        ax.set_xlabel(L['time_min'], fontsize=9)
        ax.set_ylabel(L['hr_label_short'], fontsize=9)
        ax.set_ylim(60, hr_max + 15)
    # Hide unused axes
    for j in range(len(dates), len(axes) if hasattr(axes, '__len__') else 1):
        axes[j].axis('off')
    plt.tight_layout()
    out = os.path.join(charts_dir, '09_hr_traces.png')
    plt.savefig(out, dpi=140, bbox_inches='tight')
    plt.close()
    return out


def chart_power_traces(parsed_sessions, summaries, context, charts_dir, lang='id'):
    L = _L(lang)
    by_date = {p['date_iso']: p for p in parsed_sessions if p['date_iso']}
    pdates = [d for d in sorted(summaries.keys()) if summaries[d].get('has_power')]
    if not pdates:
        return None
    ftp = context['ftp']

    n = len(pdates)
    fig, axes = plt.subplots(n, 1, figsize=(10, 2.5*n))
    if n == 1:
        axes = [axes]
    for idx, d in enumerate(pdates):
        ax = axes[idx]
        recs = by_date[d]['records']
        pwrs = [r.get('power') for r in recs if r.get('power') is not None]
        if not pwrs:
            continue
        t = np.arange(len(pwrs)) / 60.0
        ax.plot(t, pwrs, color=COLORS['primary'], linewidth=0.4, alpha=0.6)
        window = 30
        if len(pwrs) > window:
            roll = np.convolve(pwrs, np.ones(window)/window, mode='valid')
            ax.plot(t[window-1:], roll, color=COLORS['danger'], linewidth=1.3, label=L['avg_30s'])
        ax.axhline(ftp, color='green', linestyle='--', alpha=0.7, label=f'FTP={ftp}W')
        ax.set_title(f"{_date_label(d)} — {L['pwr_trace']}", fontsize=10, fontweight='bold')
        ax.set_xlabel(L['time_min'], fontsize=9)
        ax.set_ylabel(L['power_w'], fontsize=9)
        ax.legend(loc='upper right', fontsize=8)
        ax.set_ylim(0, max(pwrs)*1.1)
    plt.tight_layout()
    out = os.path.join(charts_dir, '10_power_traces.png')
    plt.savefig(out, dpi=140, bbox_inches='tight')
    plt.close()
    return out


def chart_elevation(parsed_sessions, summaries, charts_dir, lang='id'):
    L = _L(lang)
    by_date = {p['date_iso']: p for p in parsed_sessions if p['date_iso']}
    dates = sorted(summaries.keys())
    n = len(dates)
    cols = 2 if n > 1 else 1
    rows = (n + cols - 1) // cols
    fig, axes = plt.subplots(rows, cols, figsize=(11, 3.5*rows))
    if n == 1:
        axes = [axes]
    else:
        axes = np.array(axes).flatten()
    for idx, d in enumerate(dates):
        ax = axes[idx]
        recs = by_date[d]['records']
        alts, dists = [], []
        for r in recs:
            a = r.get('enhanced_altitude') or r.get('altitude')
            if a is not None:
                alts.append(a)
                dists.append((r.get('distance') or 0) / 1000)
        if not alts:
            ax.set_title(f"{_date_label(d)} - {L['no_elev_data']}", fontsize=10)
            continue
        ax.fill_between(dists, alts, min(alts), alpha=0.4, color=COLORS['success'])
        ax.plot(dists, alts, color='darkgreen', linewidth=1)
        asc = summaries[d].get('ascent_m', '?')
        ax.set_title(f"{_date_label(d)} — {L['elev_profile']} ({L['ascent']}: {asc}m)",
                     fontsize=10, fontweight='bold')
        ax.set_xlabel(L['distance_km_axis'], fontsize=9)
        ax.set_ylabel(L['altitude_m'], fontsize=9)
    for j in range(len(dates), len(axes) if hasattr(axes, '__len__') else 1):
        axes[j].axis('off')
    plt.tight_layout()
    out = os.path.join(charts_dir, '11_elevation.png')
    plt.savefig(out, dpi=140, bbox_inches='tight')
    plt.close()
    return out


# ----------------------------------------------------------------------
# Orchestrator
# ----------------------------------------------------------------------

def generate_all_charts(summaries, context, parsed_sessions, charts_dir, lang='id'):
    """Generate every chart and return a dict of {name: path}."""
    os.makedirs(charts_dir, exist_ok=True)
    out = {}
    out['distance_duration'] = chart_distance_duration(summaries, charts_dir, lang)
    out['heartrate']         = chart_heartrate(summaries, context, charts_dir, lang)
    out['power']             = chart_power(summaries, context, charts_dir, lang)
    out['tss_te']            = chart_tss_te(summaries, charts_dir, lang)
    out['hr_zones']          = chart_hr_zones(summaries, charts_dir, lang)
    out['pwr_zones']         = chart_power_zones(summaries, context, charts_dir, lang)
    out['power_curve']       = chart_power_curve(summaries, charts_dir, lang)
    out['speed_cadence']     = chart_speed_cadence(summaries, charts_dir, lang)
    out['hr_traces']         = chart_hr_traces(parsed_sessions, summaries, context, charts_dir, lang)
    out['power_traces']      = chart_power_traces(parsed_sessions, summaries, context, charts_dir, lang)
    out['elevation']         = chart_elevation(parsed_sessions, summaries, charts_dir, lang)
    return out
