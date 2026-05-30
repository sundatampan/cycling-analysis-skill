---
name: cycling-analysis-fit
description: "Process Garmin/Wahoo FIT files (.fit) to generate comprehensive cycling performance analysis PDF reports. Use this skill whenever the user uploads one or more .fit files and asks for analysis, assessment, training report, performance review, or wants to evaluate their cycling/bike rides. Also trigger when the user mentions analyzing power data, heart rate zones, TSS, FTP, VO2 Max, cardiac drift, training stress, or any cycling metrics from Garmin/Wahoo/Strava exports. Generates multi-page PDF with personal profile, per-session breakdown, HR/power zone distribution, peak power curves, cardiac drift detection, HR recovery analysis, and personalized training recommendations. Supports both Bahasa Indonesia and English output."
license: Proprietary
---

# Cycling Analysis from Garmin FIT Files

This skill processes one or more `.fit` files (Garmin Activity Files) and produces a polished, multi-page PDF cycling performance report with charts, zone analysis, cardiac drift detection, and personalized training recommendations.

## When to use this skill

Trigger this skill whenever the user:
- Uploads `.fit` files and asks for any kind of analysis, summary, or report
- Asks to "analyze my rides", "review my training", "make me a training report"
- Wants to evaluate cycling performance, power output, heart rate zones, TSS, FTP, or VO₂ Max
- Mentions cardiac drift, HR recovery, or HR spike issues from training data
- Requests recommendations for improving cycling power, endurance, or VO₂ Max

## Workflow at a glance

1. **Collect inputs** — gather `.fit` files and the rider's profile (name, age, weight, height, gender, VO₂ Max, FTP)
2. **Run the orchestrator** — call `scripts/run_analysis.py` once; it handles parsing, analytics, chart generation, and PDF assembly end-to-end
3. **Deliver the PDF** — present the output file to the user via `present_files`

## Step 1 — Collect inputs

The skill needs two things from the user:

### A. FIT files
Usually uploaded by the user. They land in `/mnt/user-data/uploads/`. The filename pattern is flexible — date-based names like `09-05-2026.fit` work well because they get sorted chronologically, but any filename is fine.

### B. Rider profile
Ask the user (or extract from conversation context) for:
- **Name** (required) — appears on cover page
- **Age** (required) — for HR max estimation if not provided
- **Weight in kg** (required) — for W/kg calculations
- **Height in cm** (optional)
- **Gender** (optional — `male` or `female`)
- **VO₂ Max** (optional) — if known from prior testing
- **FTP in watts** (optional) — if known; otherwise the skill estimates from data
- **HR Max** (optional) — if measured; otherwise estimated from data + Tanaka formula
- **Medical notes** (optional) — short string of relevant medical context (e.g., "Type 2 diabetes, well-controlled") to tailor recommendations

If the user provides all this in the conversation, just use it. If anything required is missing, ask once briefly before running.

## Step 2 — Run the orchestrator

Use a JSON config file because it's cleaner than long CLI args. Create `/home/claude/cycling_config.json`:

```json
{
  "name": "I Wayan Mertha",
  "age": 57,
  "weight_kg": 85,
  "height_cm": 175,
  "gender": "male",
  "vo2max_cycling": 38.0,
  "vo2max_running": 38.0,
  "ftp_watts": 175,
  "hr_max": null,
  "language": "id",
  "medical_notes": null,
  "fit_files_dir": "/mnt/user-data/uploads",
  "output_pdf": "/mnt/user-data/outputs/Laporan_Analisis_Cycling.pdf"
}
```

Field rules:
- `language`: `"id"` for Bahasa Indonesia, `"en"` for English. Default to `"id"` unless the user clearly prefers English.
- `hr_max`: leave as `null` to auto-estimate (uses max observed in data, falling back to 208 − 0.7×age)
- `ftp_watts`: leave as `null` to auto-estimate from 20-minute best power × 0.95
- `medical_notes`: short context string that gets woven into the recommendations section. Set to `null` if none.
- `fit_files_dir`: directory containing the `.fit` files; the skill picks them up automatically and sorts by date in filename when possible
- `output_pdf`: must be inside `/mnt/user-data/outputs/` so it can be presented to the user

Then run:

```bash
python /home/claude/cycling-analysis-fit/scripts/run_analysis.py --config /home/claude/cycling_config.json
```

The orchestrator handles everything: FIT parsing, zone computation, cardiac drift detection, HR recovery analysis, chart rendering, and PDF assembly. It prints progress and a summary table to stdout. Output PDF is typically 9–14 pages depending on number of sessions.

## Step 3 — Deliver the PDF

After the script completes, use `present_files` with the output path. Add a short summary of the most interesting findings (best session, any red-flag patterns, top 2–3 recommendations) — don't repeat the whole report, just orient the user to what's inside.

## What the report contains

Every report has the same structure so it's predictable:

1. **Cover** — rider profile, VO₂ Max classification, FTP context
2. **Executive summary** — cumulative totals + per-session table + top findings
3. **Per-session analysis** — distance/duration, HR, power, TSS/Training Effect, HR zone distribution, power zone distribution, peak power curve, speed/cadence, elevation profile (one chart per topic, captioned)
4. **Recommendations** — five prioritized actions, weekly program template, recovery/nutrition guidance, 3- and 6-month targets, ongoing measurement plan
5. **Notes** — medical caveat and (if `medical_notes` was provided) tailored guidance

## Adapting to context

A few situations come up often:

**The user has just one FIT file.** Still works — the report just has fewer per-session comparisons. The peak power curve chart adapts.

**A FIT file has no power data.** Power-specific charts skip that session gracefully; HR-based analysis still runs.

**The user provides medical context** (diabetes, hypertension, recent illness). Pass it in `medical_notes` and the recommendations section adapts — e.g., for diabetes it switches off high-intensity VO₂ Max work and emphasizes Zone 2 with glucose monitoring guidance.

**Subsequent runs for the same rider.** The skill is stateless. Just update the config (especially `output_pdf` filename so you don't overwrite) and rerun.

**Different language.** Set `language: "en"` for English. All chart titles, labels, and report text switch.

## File layout

```
cycling-analysis-fit/
├── SKILL.md                       (this file)
├── scripts/
│   ├── run_analysis.py            (orchestrator — call this)
│   ├── parse_fit.py               (FIT → structured data)
│   ├── analyze.py                 (analytics + cardiac drift + HR recovery)
│   ├── make_charts.py             (matplotlib charts)
│   └── make_pdf.py                (reportlab PDF assembly)
└── references/
    ├── training_zones.md          (HR + power zone formulas)
    └── recommendations.md         (template recommendations + medical adaptations)
```

The reference files document the formulas and templates used by the scripts. Read them only if the user asks "how did you calculate X" or wants to modify the methodology.

## Dependencies

Python packages: `fitparse`, `numpy`, `matplotlib`, `reportlab`. All standard in the claude.ai code execution environment. If any is missing, install with `pip install <pkg> --break-system-packages`.
