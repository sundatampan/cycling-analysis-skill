# Training Zones Reference

This document explains the formulas the skill uses for HR and Power zones. Read this if the user asks how a metric was computed, or wants to tweak the methodology.

## Heart Rate Zones (5-zone model)

Based on percentage of **HR Max**:

| Zone | Range (% HR Max) | Description | Bahasa Indonesia |
|------|------------------|-------------|------------------|
| Z1   | < 60%           | Recovery    | Pemulihan        |
| Z2   | 60–70%          | Endurance   | Daya tahan       |
| Z3   | 70–80%          | Tempo       | Tempo            |
| Z4   | 80–90%          | Threshold   | Ambang batas     |
| Z5   | ≥ 90%           | VO₂ Max     | VO₂ Max          |

### HR Max estimation

The skill picks HR Max in this order:
1. If user provides `hr_max` in config → use it.
2. Otherwise, use the **highest HR observed across sessions + 5 bpm buffer**, but not below the Tanaka estimate.
3. Tanaka formula fallback: `HR Max = 208 − 0.7 × age` (more accurate than 220 − age for masters athletes).

The +5 bpm buffer prevents Z5 from being underpopulated when the rider hasn't truly maxed out in the captured sessions.

## Power Zones (7-zone Coggan model)

Based on percentage of **FTP** (Functional Threshold Power):

| Zone | Range (% FTP) | Description       | Bahasa Indonesia    |
|------|---------------|-------------------|---------------------|
| Z1   | < 55%        | Active Recovery   | Pemulihan Aktif     |
| Z2   | 55–75%       | Endurance         | Daya tahan          |
| Z3   | 75–90%       | Tempo             | Tempo               |
| Z4   | 90–105%      | Threshold         | Ambang batas        |
| Z5   | 105–120%     | VO₂ Max           | VO₂ Max             |
| Z6   | 120–150%     | Anaerobic         | Anaerobik           |
| Z7   | > 150%       | Neuromuscular     | Neuromuskular       |

### FTP estimation

In order:
1. If user provides `ftp_watts` → use it.
2. Otherwise: best 20-minute average power across all sessions × 0.95 (standard FTP estimation formula).
3. Fallback if no 20-min sample available: 150 W (conservative amateur baseline).

**Note on overestimated device FTP:** Garmin/Wahoo head units sometimes report a `threshold_power` field that overestimates real FTP. The skill prefers user-provided or 20-min-derived values for that reason.

## Cardiac Drift Detection

For each session with power data, the skill compares HR at the same power level between the **first half** and **second half**:

```
drift = mean(HR in 2nd half at power band P) - mean(HR in 1st half at power band P)
```

Bands checked: 60–100W, 100–150W (typical cruising ranges).

**Thresholds:**
- < +5 bpm → normal
- +5 to +10 bpm → mild (watch hydration)
- > +10 bpm → significant (common causes: dehydration, glycogen depletion, heat stress, fatigue, or cardiac issues)

A persistent pattern of high drift across multiple sessions warrants medical evaluation.

## HR Recovery on Coasting

Looks for moments where power dropped to <30W for ≥30 seconds (rider stopped pedaling — e.g., reaching a stoplight or descending), then measures:

- **30-second drop:** HR at start of coast minus HR 30 seconds later
- **60-second drop:** same, but 60 seconds later

**Reference values** (healthy 50+ year-old cyclist):
- 30s drop: 15–25+ bpm = normal
- 60s drop: 22+ bpm = normal; < 12 bpm = possible cardiac autonomic dysfunction

This is a different (and more reliable for cycling) version of the standard clinical Heart Rate Recovery (HRR) test, which is usually done after treadmill cessation.

## Peak Power Curve

For each session, the skill computes the best **rolling-average power** for:
- 5 seconds → sprint capacity (anaerobic)
- 1 minute → anaerobic capacity
- 5 minutes → VO₂ Max capacity
- 20 minutes → threshold capacity (used for FTP estimate)

Useful for tracking which energy systems are improving.

## VO₂ Max Classification

Uses Cooper Institute reference ranges by age and gender. Categories (low to high):
**Buruk** (Poor) → **Kurang** (Below avg) → **Cukup** (Average) → **Baik** (Good) → **Sangat Baik** (Excellent) → **Superior**.

For a 50–59-year-old male:
- < 18 → Buruk
- 18–24 → Kurang
- 25–30 → Cukup
- 31–41 → Baik
- 42–49 → Sangat Baik
- ≥ 50 → Superior

## TSS, IF, NP — Standard Definitions

These come straight from the FIT file (computed by the head unit), so the skill doesn't recompute them. For reference:

- **Normalized Power (NP):** A weighted average that accounts for the non-linear physiological cost of variable power output. ≈ 4th-root mean of 4th-power moving average.
- **Intensity Factor (IF):** NP / FTP.
- **TSS (Training Stress Score):** `(duration_seconds × NP × IF) / (FTP × 3600) × 100`. A 1-hour ride at FTP = 100 TSS.

TSS interpretation:
- < 150 → easy day, fully recovered next morning
- 150–300 → moderate, full recovery in 1–2 days
- 300–450 → hard, recovery in 2–4 days
- > 450 → very hard, recovery in 5+ days
