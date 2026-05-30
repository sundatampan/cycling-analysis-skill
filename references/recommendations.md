# Recommendations Reference

This document explains how the recommendation templates in the PDF are structured and how they adapt to medical context.

## Standard Recommendations (Default Profile)

The PDF always includes 5 prioritized actions. These are calibrated for **masters athletes (40+)** who want to improve cycling power & VO₂ Max:

1. **Fix Cadence to 85–95 rpm** — low cadence loads the leg muscles instead of the cardiovascular system. Fastest-impact change.
2. **VO₂ Max Intervals (5×5 min @ 110–120% FTP)** — the single most effective stimulus for VO₂ Max improvement.
3. **Sweet Spot / Threshold (2×20 min @ 88–94% FTP)** — builds FTP, the foundation of all power improvements.
4. **Long Endurance Ride (2–3 h in Z2)** — builds mitochondria and base aerobic capacity.
5. **Strength Training 2×/week** — critical after age 50 to fight sarcopenia, improves cycling efficiency 5–7%.

## Medical Adaptations

When `medical_notes` contains certain keywords, the skill modifies recommendations:

### Diabetes / DM / "gula darah tinggi"
- **Priority #2 (VO₂ Max intervals) is REPLACED** with a cautious version that says to wait for physician clearance and focus on Z2 + strength first.
- The cover page shows the medical note prominently.
- The cardiac alert section is more likely to fire since diabetes affects HR autonomic response.

### Hypertension / "hipertensi" / "tekanan darah tinggi"
- Currently no automatic adaptation in the skill, but the medical note is displayed prominently. (Future improvement: add a warning around HR-based intensity targeting.)

### Recent illness / "demam" / "flu" / "recent surgery"
- Currently no automatic adaptation. (Future: add explicit return-to-training progression guidance.)

## How to extend medical adaptations

The medical adaptation logic lives in `make_pdf.py` inside `build_pdf()`:

```python
medical = (profile.get('medical_notes') or '').lower()
has_diabetes = any(k in medical for k in ['diabet', 'diabetes', 'dm', 'gula darah tinggi'])
```

To add a new condition (e.g., "asthma"):
1. Add a detection variable: `has_asthma = 'asma' in medical or 'asthma' in medical`
2. In the priorities loop, add a conditional rewrite of the relevant priority text.
3. Document the new keyword here.

## Weekly Program Template

The 8-week sample program (in `TEXTS['id']['week_rows']` and `TEXTS['en']['week_rows']`) is calibrated for ~300–380 TSS/week, which is appropriate for serious amateur masters athletes with 6–8 training hours available.

For different volume targets, adjust:
- **Lower volume (200–280 TSS/week):** drop Friday strength or move long ride to 1.5–2 h.
- **Higher volume (400–500 TSS/week):** add a second endurance ride on Wednesday or extend Saturday to 4 h.

## 3- and 6-Month Targets

The skill generates target values dynamically based on current bests:

| Metric | 3-Month Target | 6-Month Target |
|--------|----------------|----------------|
| FTP | +15% | +30% |
| VO₂ Max | +3 ml/kg/min | +6 ml/kg/min |
| 5-min power | +20% | +40% |
| 1-min power | +15% | +30% |
| Cadence | current +10 rpm (cap at 90) | 88–92 rpm |
| Body weight | −3 kg | −5 kg |

These targets are aggressive but achievable for an athlete starting from a recreational base with consistent training. For already-trained athletes (FTP > 3.5 W/kg), targets should be halved (e.g., +7% in 3 months instead of +15%).

## Footer

Every report ends with a footer reminding the user:
- The report is generated automatically
- It doesn't replace medical advice
- They should consult a certified coach and sports physician for personalization

This is non-negotiable boilerplate — keep it on every report regardless of language.
