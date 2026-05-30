# 🚴 cycling-analysis-fit

**A Claude Skill that turns Garmin/Wahoo `.FIT` files into a comprehensive cycling performance PDF report — automatically.**

Upload your `.fit` files → get a polished 10+ page PDF with HR zones, power analysis, cardiac drift detection, peak power curves, and personalized training recommendations.

![Python](https://img.shields.io/badge/Python-3.11+-blue?logo=python)
![Claude Skill](https://img.shields.io/badge/Claude-Skill-orange)
![License](https://img.shields.io/badge/License-Proprietary-red)
![Language](https://img.shields.io/badge/Language-ID%20%7C%20EN-green)

---

## 📄 Sample Output

> Drop your `.fit` files and get a report like this in minutes:

| Cover & Profile | HR Zone Distribution | Peak Power Curve | Recommendations |
|---|---|---|---|
| *(see `examples/sample_report.pdf`)* | Zone 1–5 breakdown per session | 5s / 1min / 5min / 20min bests | 5 prioritized actions + 8-week program |

---

## ✨ What the Report Contains

1. **Cover Page** — Rider profile, VO₂ Max classification, FTP context
2. **Executive Summary** — Cumulative totals, per-session table, top findings
3. **Per-Session Analysis** (one section per ride):
   - Distance, duration, HR avg/max
   - Power avg, Normalized Power, max power
   - TSS & Training Effect (aerobic + anaerobic)
   - HR Zone distribution chart
   - Power Zone distribution chart (Coggan 7-zone)
   - Peak Power Curve (5s, 1min, 5min, 20min)
   - Speed & Cadence profile
   - Elevation profile
4. **Cardiac Drift Detection** — flags dehydration/heat stress signals
5. **HR Recovery Analysis** — autonomic fitness indicator
6. **Training Recommendations** — 5 high-impact priorities, 8-week weekly program, 3 & 6-month targets
7. **Medical Notes** (if provided) — adapts recommendations accordingly

---

## 🚀 Quick Start

### Prerequisites

```bash
pip install fitparse numpy matplotlib reportlab
```

Python 3.11+ required.

### 1. Install the Skill

Download `cycling-analysis-fit.skill` (the zip bundle) and drop it into your Claude workspace skills folder, or install manually:

```bash
unzip cycling-analysis-fit.skill -d ~/claude-skills/
```

### 2. Create a Config File

Create `cycling_config.json`:

```json
{
  "name": "Your Name",
  "age": 35,
  "weight_kg": 70,
  "height_cm": 170,
  "gender": "male",
  "vo2max_cycling": null,
  "ftp_watts": null,
  "hr_max": null,
  "language": "id",
  "medical_notes": null,
  "fit_files_dir": "/path/to/your/fit/files",
  "output_pdf": "/path/to/output/report.pdf"
}
```

**Config fields:**

| Field | Required | Notes |
|---|---|---|
| `name` | ✅ | Appears on cover page |
| `age` | ✅ | Used for HR max estimation |
| `weight_kg` | ✅ | For W/kg calculations |
| `height_cm` | optional | |
| `gender` | optional | `"male"` or `"female"` |
| `vo2max_cycling` | optional | ml/kg/min — if known |
| `ftp_watts` | optional | Auto-estimated if `null` (best 20-min power × 0.95) |
| `hr_max` | optional | Auto-estimated from data + Tanaka formula if `null` |
| `language` | optional | `"id"` (Bahasa Indonesia) or `"en"` (English). Default: `"id"` |
| `medical_notes` | optional | e.g. `"Type 2 diabetes, well-controlled"` — adapts recommendations |
| `fit_files_dir` | ✅ | Directory containing `.fit` files |
| `output_pdf` | ✅ | Output path for the PDF report |

### 3. Run

```bash
python scripts/run_analysis.py --config cycling_config.json
```

The script handles everything end-to-end: FIT parsing → zone computation → cardiac drift detection → chart generation → PDF assembly.

---

## 📁 File Structure

```
cycling-analysis-fit/
├── SKILL.md                        # Claude Skill descriptor
├── scripts/
│   ├── run_analysis.py             # Orchestrator — run this
│   ├── parse_fit.py                # FIT binary → structured data
│   ├── analyze.py                  # Analytics, cardiac drift, HR recovery
│   ├── make_charts.py              # Matplotlib chart generation
│   └── make_pdf.py                 # ReportLab PDF assembly
└── references/
    ├── training_zones.md           # HR & Power zone formulas
    └── recommendations.md          # Recommendation templates & medical adaptations
```

---

## 🧠 How It Works

### FIT File Parsing
Uses [`fitparse`](https://github.com/dtcooper/python-fitparse) to decode binary Garmin FIT format into structured records (timestamp, HR, power, cadence, speed, GPS, elevation).

### Zone Computation
- **HR Zones** — 5-zone model based on % HR Max (Tanaka formula fallback: `208 − 0.7 × age`)
- **Power Zones** — Coggan 7-zone model based on % FTP
- **FTP Auto-estimation** — best 20-minute average power × 0.95

### Cardiac Drift Detection
Compares average HR at the same power band between the first and second half of each session:
- < 5 bpm drift → normal
- 5–10 bpm → mild (watch hydration)
- \> 10 bpm → significant (flag for dehydration, heat stress, or fatigue)

### HR Recovery Analysis
Detects coasting moments (power < 30W for ≥ 30 seconds) and measures HR drop at 30s and 60s — a reliable indicator of cardiac autonomic fitness.

### Medical Adaptations
Pass `medical_notes` in the config and the recommendation section adapts. Currently supported: diabetes/DM (replaces high-intensity VO₂ Max work with physician-clearance guidance and Zone 2 focus).

---

## 📊 Example Insights (Real Data)

From 5 sessions, 180 km, 2,400 m elevation:

- ⚠️ **65% of time in Zone 1 (Recovery)** — training lacks structure
- ⚠️ **Average cadence 68 rpm** — optimal is 85–95; fixing this alone could add 10–15% power
- ⚠️ **Cardiac drift detected** in multiple sessions — likely heat stress in Indonesian climate

---

## 🌐 Language Support

Set `"language": "id"` for full Bahasa Indonesia output (all chart labels, section headers, recommendations).  
Set `"language": "en"` for English.

---

## 🔧 Compatible Devices

Any device that exports standard `.FIT` files:
- Garmin Edge series (530, 830, 1030, etc.)
- Garmin Forerunner / Fenix (with cycling activity)
- Wahoo ELEMNT / ROAM / BOLT
- Strava export (`.fit` format)

---

## ⚠️ Disclaimer

This report is generated automatically from Garmin FIT data. It does **not** replace professional medical advice. Consult a certified cycling coach and sports physician before starting high-intensity training programs.

---

## 🤝 Contributing

Pull requests are welcome. For major changes, open an issue first.

Ideas for future improvements:
- [ ] HRV trend analysis
- [ ] Multi-week CTL/ATL/TSB fitness curve
- [ ] Strava API integration (direct import without manual .fit download)
- [ ] Web UI for non-technical users

---

## 👤 Author

Built by **Ari Setiawan** — product engineer & road cyclist based in Indonesia.

[![LinkedIn](https://img.shields.io/badge/LinkedIn-Connect-blue?logo=linkedin)](https://linkedin.com/in/arisetiawan-blibli/)
[![GitHub](https://img.shields.io/badge/GitHub-Follow-black?logo=github)](https://github.com/sundatampan)
