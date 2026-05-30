"""
make_pdf.py
===========
Build the cycling analysis PDF report from summaries + charts.

Usage:
    from make_pdf import build_pdf
    build_pdf(summaries, context, charts, profile, output_path, lang='id')
"""

import os
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Image, PageBreak, Table, TableStyle,
)
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY

from analyze import classify_vo2max

PRIMARY = colors.HexColor('#1f4e79')
ACCENT  = colors.HexColor('#c00000')
LIGHT   = colors.HexColor('#deebf7')
GRAY    = colors.HexColor('#595959')


# ----------------------------------------------------------------------
# i18n strings
# ----------------------------------------------------------------------

TEXTS = {
    'id': {
        'title': 'LAPORAN ANALISIS LATIHAN BERSEPEDA',
        'subtitle': 'Evaluasi {n} Sesi Garmin FIT',
        'athlete_info': 'INFORMASI ATLET',
        'name': 'Nama',
        'age': 'Usia',
        'age_unit': 'tahun',
        'gender': 'Jenis Kelamin',
        'male': 'Laki-laki',
        'female': 'Perempuan',
        'height': 'Tinggi Badan',
        'weight': 'Berat Badan',
        'bmi': 'BMI',
        'bmi_note': '(Berat normal: 18,5–25)',
        'vo2_cycling': 'VO2 Max (Bersepeda)',
        'vo2_running': 'VO2 Max (Lari)',
        'hr_max_label': 'Estimasi HR Maksimum',
        'hr_max_note': '(berdasarkan data sesi)',
        'ftp_label': 'FTP Acuan',
        'vo2_class': 'Klasifikasi',
        'sec_summary': '1. RINGKASAN EKSEKUTIF',
        'summary_intro': 'Laporan ini menganalisis {n} sesi latihan bersepeda dengan total jarak <b>{km:.1f} km</b> dalam <b>{h} jam {m} menit</b> waktu aktif dan total elevasi naik <b>{asc} m</b>.',
        'col_date': 'Tanggal',
        'col_dist': 'Jarak',
        'col_dur': 'Durasi',
        'col_avg_hr': 'Avg HR',
        'col_avg_pwr': 'Avg Power',
        'col_np': 'NP',
        'col_tss': 'TSS',
        'col_te': 'TE',
        'findings_title': 'Temuan Utama:',
        'sec_per_session': '2. ANALISIS PER SESI LATIHAN',
        'sec_2_1': '2.1 Jarak Tempuh & Durasi',
        'sec_2_2': '2.2 Detak Jantung (Heart Rate)',
        'sec_2_3': '2.3 Output Power',
        'sec_2_4': '2.4 Training Load (TSS) & Training Effect',
        'sec_2_5': '2.5 Distribusi Zona Detak Jantung',
        'sec_2_6': '2.6 Distribusi Zona Power',
        'sec_2_7': '2.7 Kurva Power Puncak',
        'sec_2_8': '2.8 Kecepatan & Cadence',
        'sec_2_9': '2.9 Profil Elevasi',
        'caption_1': 'Gambar 1. Perbandingan jarak dan durasi sesi.',
        'caption_2': 'Gambar 2. Detak jantung rata-rata dan maksimum per sesi.',
        'caption_3': 'Gambar 3. Profil detak jantung dari waktu ke waktu pada setiap sesi.',
        'caption_4': 'Gambar 4. Power rata-rata, Normalized Power, dan power maksimum per sesi.',
        'caption_5': 'Gambar 5. Profil power tiap sesi (garis tipis = power per detik, garis tebal = rata-rata 30 detik).',
        'caption_6': 'Gambar 6. TSS dan Training Effect aerobik/anaerobik.',
        'caption_7': 'Gambar 7. Persentase waktu di setiap zona detak jantung.',
        'caption_8': 'Gambar 8. Distribusi waktu di zona power (acuan FTP = {ftp} W).',
        'caption_9': 'Gambar 9. Power puncak yang dipertahankan untuk durasi tertentu.',
        'caption_10': 'Gambar 10. Kecepatan dan cadence rata-rata/maksimum.',
        'caption_11': 'Gambar 11. Profil elevasi setiap sesi.',
        'sec_reco': '3. REKOMENDASI UNTUK MENINGKATKAN POWER & VO2 MAX',
        'reco_intro': 'Berdasarkan analisis sesi di atas dan profil atlet, berikut adalah program peningkatan terstruktur. Penelitian menunjukkan atlet usia matang masih dapat meningkatkan VO2 Max sebesar 10\u201320% dalam 12 minggu dengan latihan yang tepat.',
        'sec_3_1': '3.1 Lima Prioritas Utama (Berdampak Tinggi)',
        'sec_3_2': '3.2 Contoh Program Mingguan (8 Minggu)',
        'sec_3_3': '3.3 Pemulihan & Nutrisi',
        'sec_3_4': '3.4 Target Pengembangan 3 & 6 Bulan',
        'sec_3_5': '3.5 Pengukuran Berkelanjutan',
        'sec_3_6': '3.6 Catatan Penting',
        'medical_warning': '<b>Catatan medis:</b> {notes}',
        'footer': '<i>Laporan ini dibuat otomatis dari analisis data Garmin FIT. Tidak menggantikan saran medis profesional. Konsultasikan program latihan dengan pelatih bersertifikat dan dokter olahraga untuk personalisasi optimal.</i>',
        'cardiac_alert': '<b>\u26a0 Perhatian:</b> Analisis menemukan tanda-tanda cardiac drift (HR naik meski power tidak naik) atau pemulihan HR yang lambat di beberapa sesi. Detail ada di bagian per-sesi. Jika ini sudah terasa dalam latihan (HR \"spike\" yang sulit turun), konsultasi dokter direkomendasikan sebelum melanjutkan intensitas tinggi.',
        'priorities': [
            ('1. Perbaiki Cadence ke 85\u201395 rpm',
             'Cadence rendah membebani otot kaki (lebih cepat lelah) alih-alih kardiovaskular. Drill: 3\u00d71 menit di cadence 100+ rpm setiap warm-up. Pasang alert di Garmin jika cadence <80 rpm. Dalam 2\u20134 minggu cadence alami naik.'),
            ('2. Latihan Interval VO2 Max (1\u00d7 per minggu)',
             'Pemanasan 15 menit \u2192 <b>5\u00d75 menit</b> di 110\u2013120% FTP (Zona 5 HR) dengan istirahat 3 menit di Zona 1. Pendinginan 10 menit. Ini rangsangan paling efektif untuk meningkatkan VO2 Max.'),
            ('3. Latihan Sweet Spot / Threshold (1\u00d7 per minggu)',
             '2\u00d720 menit atau 3\u00d715 menit di 88\u201394% FTP (Zona 4 bawah). Membangun FTP yang merupakan fondasi semua peningkatan power.'),
            ('4. Long Endurance Ride (1\u00d7 per minggu)',
             '2\u20133 jam di Zona 2 (60\u201370% HR maks), cadence 85+ rpm. Tetap di Z2, jangan tergoda naik. Membangun mitochondria & kapasitas aerobik dasar.'),
            ('5. Strength Training 2\u00d7 per minggu',
             'Squat, deadlift, leg press, lunges, single-leg press. 3\u20134 set \u00d7 6\u201310 repetisi @ 70\u201380% 1RM. Meningkatkan efisiensi bersepeda 5\u20137% pada atlet usia matang.'),
        ],
        'week_header': ['Hari', 'Latihan', 'Durasi', 'Intensitas', 'TSS Target'],
        'week_rows': [
            ('Senin', 'Istirahat / Stretching ringan', '—', '—', '0'),
            ('Selasa', 'Interval VO2 Max (5\u00d75 menit)', '75 mnt', 'Z5 / 110-120% FTP', '70-85'),
            ('Rabu', 'Recovery Ride', '45-60 mnt', 'Z1 (<105 bpm)', '25-35'),
            ('Kamis', 'Sweet Spot (2\u00d720 mnt) atau Threshold', '75-90 mnt', 'Z3-Z4 / 88-94% FTP', '70-90'),
            ('Jumat', 'Strength Training (kaki & core)', '45-60 mnt', 'Beban 70-80% 1RM', '—'),
            ('Sabtu', 'Long Endurance Ride', '2-3 jam', 'Z2, cadence 85+', '90-130'),
            ('Minggu', 'Spin Mudah atau Cross-Train', '45-60 mnt', 'Z1-Z2', '20-40'),
        ],
        'week_note': '<b>Total TSS mingguan target: ~300\u2013380.</b> Periodisasi: 3 minggu naik \u2192 1 minggu deload. Tes FTP setiap 6\u20138 minggu.',
        'recovery_items': [
            '<b>Tidur 7\u20139 jam:</b> hormon pertumbuhan untuk pemulihan otot dilepaskan saat tidur dalam.',
            '<b>Protein 1,6\u20132,0 g/kg/hari:</b> usia matang perlu lebih banyak protein untuk menjaga massa otot. Pisahkan ke 4\u20135 porsi.',
            '<b>Karbohidrat 5\u20137 g/kg/hari</b> di hari latihan keras. 30\u201360 g/jam selama ride &gt;90 menit.',
            '<b>Hidrasi:</b> 500\u2013750 ml/jam di cuaca panas Indonesia. Tambahkan elektrolit (natrium 400\u2013800 mg/jam).',
            '<b>Stretching & mobility:</b> 15 menit/hari fokus pada hip flexor, hamstring, lower back, IT band.',
            '<b>Pantau HRV (Heart Rate Variability):</b> indikator pemulihan harian.',
        ],
        'target_header': ['Metrik', 'Saat Ini', 'Target 3 Bulan', 'Target 6 Bulan'],
        'measure_items': [
            '<b>Tes FTP setiap 6\u20138 minggu:</b> 20 menit all-out \u2192 FTP = 0,95 \u00d7 avg power.',
            '<b>Catat resting HR setiap pagi:</b> kenaikan &gt;7 bpm = perlu hari istirahat.',
            '<b>Pantau Training Load (CTL):</b> target ~50\u201370 untuk amatir aktif.',
            '<b>Health metrics tahunan:</b> tes darah lengkap (hematocrit, ferritin, vit D, B12, testosteron).',
            '<b>Bike fit profesional:</b> investasi sekali membuka power 5\u201310%.',
        ],
        'notes_med': '<b>Konsultasi medis:</b> Sebelum memulai latihan intensitas tinggi, lakukan pemeriksaan jantung (EKG, treadmill test).',
        'notes_progress': '<b>Progresi bertahap:</b> Mulai dengan 1 sesi interval di minggu 1\u20132, tambah ke 2 sesi mulai minggu 3.',
        'notes_climate': '<b>Iklim Indonesia:</b> Latihan interval terbaik dilakukan pagi (sebelum jam 8) atau sore (setelah jam 16) untuk menghindari heat stress.',
    },
    'en': {
        'title': 'CYCLING TRAINING ANALYSIS REPORT',
        'subtitle': 'Evaluation of {n} Garmin FIT Sessions',
        'athlete_info': 'ATHLETE INFORMATION',
        'name': 'Name',
        'age': 'Age',
        'age_unit': 'years',
        'gender': 'Gender',
        'male': 'Male',
        'female': 'Female',
        'height': 'Height',
        'weight': 'Weight',
        'bmi': 'BMI',
        'bmi_note': '(Normal weight: 18.5–25)',
        'vo2_cycling': 'VO2 Max (Cycling)',
        'vo2_running': 'VO2 Max (Running)',
        'hr_max_label': 'Estimated Max HR',
        'hr_max_note': '(based on session data)',
        'ftp_label': 'FTP Reference',
        'vo2_class': 'Classification',
        'sec_summary': '1. EXECUTIVE SUMMARY',
        'summary_intro': 'This report analyzes {n} cycling training sessions with a total distance of <b>{km:.1f} km</b> over <b>{h}h {m}min</b> of active time, with total ascent of <b>{asc} m</b>.',
        'col_date': 'Date',
        'col_dist': 'Distance',
        'col_dur': 'Duration',
        'col_avg_hr': 'Avg HR',
        'col_avg_pwr': 'Avg Power',
        'col_np': 'NP',
        'col_tss': 'TSS',
        'col_te': 'TE',
        'findings_title': 'Key Findings:',
        'sec_per_session': '2. PER-SESSION ANALYSIS',
        'sec_2_1': '2.1 Distance & Duration',
        'sec_2_2': '2.2 Heart Rate',
        'sec_2_3': '2.3 Power Output',
        'sec_2_4': '2.4 Training Load (TSS) & Training Effect',
        'sec_2_5': '2.5 Heart Rate Zone Distribution',
        'sec_2_6': '2.6 Power Zone Distribution',
        'sec_2_7': '2.7 Peak Power Curve',
        'sec_2_8': '2.8 Speed & Cadence',
        'sec_2_9': '2.9 Elevation Profile',
        'caption_1': 'Figure 1. Distance and duration comparison across sessions.',
        'caption_2': 'Figure 2. Average and maximum heart rate per session.',
        'caption_3': 'Figure 3. Heart rate trace over time for each session.',
        'caption_4': 'Figure 4. Average, normalized, and maximum power per session.',
        'caption_5': 'Figure 5. Power trace per session (thin = per-second, thick = 30s rolling avg).',
        'caption_6': 'Figure 6. TSS and aerobic/anaerobic Training Effect.',
        'caption_7': 'Figure 7. Time percentage in each heart rate zone.',
        'caption_8': 'Figure 8. Time distribution in power zones (FTP = {ftp} W).',
        'caption_9': 'Figure 9. Peak power sustained for various durations.',
        'caption_10': 'Figure 10. Average and maximum speed and cadence.',
        'caption_11': 'Figure 11. Elevation profile per session.',
        'sec_reco': '3. RECOMMENDATIONS TO IMPROVE POWER & VO2 MAX',
        'reco_intro': 'Based on the analysis above and the athlete profile, here is a structured improvement program. Research shows masters athletes can still improve VO2 Max by 10\u201320% in 12 weeks with appropriate training.',
        'sec_3_1': '3.1 Five Top Priorities (High Impact)',
        'sec_3_2': '3.2 Sample Weekly Program (8 Weeks)',
        'sec_3_3': '3.3 Recovery & Nutrition',
        'sec_3_4': '3.4 Development Targets (3 & 6 Months)',
        'sec_3_5': '3.5 Ongoing Measurement',
        'sec_3_6': '3.6 Important Notes',
        'medical_warning': '<b>Medical note:</b> {notes}',
        'footer': '<i>This report was generated automatically from Garmin FIT data analysis. It does not replace professional medical advice. Consult a certified cycling coach and sports physician for optimal personalization.</i>',
        'cardiac_alert': '<b>\u26a0 Attention:</b> Analysis detected cardiac drift (HR climbing despite stable power) or slow HR recovery in some sessions. Details are in the per-session section. If this is being felt in training (HR spikes that are slow to drop), medical consultation is recommended before continuing high-intensity work.',
        'priorities': [
            ('1. Fix Cadence to 85\u201395 rpm',
             'Low cadence loads the leg muscles (faster fatigue) rather than the cardiovascular system. Drill: 3\u00d71 minute at 100+ rpm in every warm-up. Set a Garmin alert if cadence &lt;80 rpm. Natural cadence rises in 2\u20134 weeks.'),
            ('2. VO2 Max Intervals (1\u00d7 per week)',
             '15 min warm-up \u2192 <b>5\u00d75 min</b> at 110\u2013120% FTP (Zone 5 HR) with 3 min recovery in Zone 1. 10 min cool-down. The most effective stimulus for VO2 Max improvement.'),
            ('3. Sweet Spot / Threshold (1\u00d7 per week)',
             '2\u00d720 min or 3\u00d715 min at 88\u201394% FTP (lower Zone 4). Builds FTP, which is the foundation of all power improvements.'),
            ('4. Long Endurance Ride (1\u00d7 per week)',
             '2\u20133 hours in Zone 2 (60\u201370% HR max), cadence 85+ rpm. Stay in Z2, don\'t drift up. Builds mitochondria and base aerobic capacity.'),
            ('5. Strength Training 2\u00d7 per week',
             'Squat, deadlift, leg press, lunges, single-leg press. 3\u20134 sets \u00d7 6\u201310 reps @ 70\u201380% 1RM. Improves cycling efficiency 5\u20137% in masters athletes.'),
        ],
        'week_header': ['Day', 'Workout', 'Duration', 'Intensity', 'TSS Target'],
        'week_rows': [
            ('Mon', 'Rest / Light Stretching', '—', '—', '0'),
            ('Tue', 'VO2 Max Intervals (5\u00d75 min)', '75 min', 'Z5 / 110-120% FTP', '70-85'),
            ('Wed', 'Recovery Ride', '45-60 min', 'Z1 (<105 bpm)', '25-35'),
            ('Thu', 'Sweet Spot (2\u00d720 min) or Threshold', '75-90 min', 'Z3-Z4 / 88-94% FTP', '70-90'),
            ('Fri', 'Strength Training (legs & core)', '45-60 min', '70-80% 1RM', '—'),
            ('Sat', 'Long Endurance Ride', '2-3 h', 'Z2, cadence 85+', '90-130'),
            ('Sun', 'Easy Spin or Cross-Train', '45-60 min', 'Z1-Z2', '20-40'),
        ],
        'week_note': '<b>Target weekly TSS: ~300\u2013380.</b> Periodization: 3 build weeks \u2192 1 deload week. FTP test every 6\u20138 weeks.',
        'recovery_items': [
            '<b>Sleep 7\u20139 hours:</b> growth hormone for muscle recovery is released in deep sleep.',
            '<b>Protein 1.6\u20132.0 g/kg/day:</b> masters athletes need more protein. Split into 4\u20135 servings.',
            '<b>Carbs 5\u20137 g/kg/day</b> on hard days. 30\u201360 g/hour during rides &gt;90 min.',
            '<b>Hydration:</b> 500\u2013750 ml/hour in hot climates. Add electrolytes (sodium 400\u2013800 mg/hour).',
            '<b>Stretching & mobility:</b> 15 min/day focus on hip flexor, hamstring, lower back, IT band.',
            '<b>Monitor HRV:</b> daily recovery indicator.',
        ],
        'target_header': ['Metric', 'Current', '3-Month Target', '6-Month Target'],
        'measure_items': [
            '<b>FTP test every 6\u20138 weeks:</b> 20-min all-out \u2192 FTP = 0.95 \u00d7 avg power.',
            '<b>Record resting HR every morning:</b> rise &gt;7 bpm = rest day needed.',
            '<b>Track Training Load (CTL):</b> target ~50\u201370 for active amateur.',
            '<b>Annual health metrics:</b> full blood panel (hematocrit, ferritin, vit D, B12, testosterone).',
            '<b>Professional bike fit:</b> one-time investment unlocks 5\u201310% power.',
        ],
        'notes_med': '<b>Medical consultation:</b> Before high-intensity training, get a cardiac exam (ECG, treadmill test).',
        'notes_progress': '<b>Gradual progression:</b> Start with 1 interval session in weeks 1\u20132, then 2 sessions from week 3.',
        'notes_climate': '<b>Climate adaptation:</b> Interval sessions are best done in cool hours to avoid heat stress.',
    },
}


# ----------------------------------------------------------------------
# Builder
# ----------------------------------------------------------------------

def build_pdf(summaries, context, charts, profile, output_path, lang='id'):
    """Assemble the PDF report.

    summaries: dict keyed by date_iso
    context:   dict with hr_max, ftp, weight_kg, age, hr_zones, pwr_zones
    charts:    dict from make_charts.generate_all_charts
    profile:   the rider profile dict
    output_path: where to write the PDF
    lang:      'id' or 'en'
    """
    T = TEXTS.get(lang, TEXTS['id'])
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    doc = SimpleDocTemplate(
        output_path, pagesize=A4,
        leftMargin=1.8*cm, rightMargin=1.8*cm,
        topMargin=1.8*cm, bottomMargin=1.8*cm,
        title=f"Cycling Analysis - {profile.get('name', '')}",
    )

    base = getSampleStyleSheet()
    title_s    = ParagraphStyle('t',  parent=base['Title'],   fontSize=22, textColor=PRIMARY, alignment=TA_CENTER, fontName='Helvetica-Bold')
    subtitle_s = ParagraphStyle('st', parent=base['Normal'],  fontSize=12, textColor=GRAY, alignment=TA_CENTER, fontName='Helvetica-Oblique', spaceAfter=18)
    h1         = ParagraphStyle('h1', parent=base['Heading1'],fontSize=16, textColor=PRIMARY, spaceBefore=14, spaceAfter=8, fontName='Helvetica-Bold')
    h2         = ParagraphStyle('h2', parent=base['Heading2'],fontSize=13, textColor=PRIMARY, spaceBefore=10, spaceAfter=6, fontName='Helvetica-Bold')
    h3         = ParagraphStyle('h3', parent=base['Heading3'],fontSize=11, textColor=ACCENT,  spaceBefore=8, spaceAfter=4, fontName='Helvetica-Bold')
    body       = ParagraphStyle('b',  parent=base['Normal'],  fontSize=10, leading=14, alignment=TA_JUSTIFY, spaceAfter=6)
    small      = ParagraphStyle('s',  parent=base['Normal'],  fontSize=9,  leading=12, textColor=GRAY)
    caption    = ParagraphStyle('cp', parent=base['Normal'],  fontSize=8,  alignment=TA_CENTER, textColor=GRAY, fontName='Helvetica-Oblique', spaceAfter=10)
    bullet     = ParagraphStyle('bu', parent=body,            leftIndent=14, bulletIndent=4, spaceAfter=3)

    story = []
    dates = sorted(summaries.keys())
    n_sessions = len(dates)

    # ============== COVER ==============
    story.append(Paragraph(T['title'], title_s))
    story.append(Paragraph(T['subtitle'].format(n=n_sessions), subtitle_s))

    bmi = profile['weight_kg'] / ((profile.get('height_cm', 170)/100.0)**2)
    vo2_cyc = profile.get('vo2max_cycling')
    vo2_run = profile.get('vo2max_running')
    age = profile.get('age', 40)
    gender = profile.get('gender', 'male')

    info_rows = [
        [T['athlete_info'], ''],
        [T['name'],   profile.get('name', '-')],
        [T['age'],    f"{age} {T['age_unit']}"],
        [T['gender'], T['male'] if gender.lower() == 'male' else T['female']],
    ]
    if profile.get('height_cm'):
        info_rows.append([T['height'], f"{profile['height_cm']} cm"])
    info_rows.append([T['weight'], f"{profile['weight_kg']} kg"])
    info_rows.append([T['bmi'],    f"{bmi:.1f} {T['bmi_note']}"])
    if vo2_cyc:
        cls = classify_vo2max(vo2_cyc, age, gender)
        info_rows.append([T['vo2_cycling'], f"{vo2_cyc} ml/kg/min ({T['vo2_class']}: {cls})"])
    if vo2_run and vo2_run != vo2_cyc:
        info_rows.append([T['vo2_running'], f"{vo2_run} ml/kg/min"])
    info_rows.append([T['hr_max_label'], f"{context['hr_max']} bpm {T['hr_max_note']}"])
    info_rows.append([T['ftp_label'], f"{context['ftp']} W ({context['ftp']/profile['weight_kg']:.2f} W/kg)"])

    info_table = Table(info_rows, colWidths=[5.5*cm, 9.5*cm])
    info_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), PRIMARY),
        ('TEXTCOLOR',  (0,0), (-1,0), colors.white),
        ('FONTNAME',   (0,0), (-1,0), 'Helvetica-Bold'),
        ('SPAN',       (0,0), (-1,0)),
        ('ALIGN',      (0,0), (-1,0), 'CENTER'),
        ('FONTNAME',   (0,1), (0,-1), 'Helvetica-Bold'),
        ('BACKGROUND', (0,1), (0,-1), LIGHT),
        ('GRID',       (0,0), (-1,-1), 0.4, colors.grey),
        ('FONTSIZE',   (0,0), (-1,-1), 10),
        ('VALIGN',     (0,0), (-1,-1), 'MIDDLE'),
        ('LEFTPADDING',(0,0), (-1,-1), 8),
        ('RIGHTPADDING',(0,0),(-1,-1), 8),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('BOTTOMPADDING',(0,0),(-1,-1), 5),
    ]))
    story.append(info_table)
    story.append(Spacer(1, 0.6*cm))

    # Medical notes (if provided)
    if profile.get('medical_notes'):
        story.append(Paragraph(T['medical_warning'].format(notes=profile['medical_notes']), small))
        story.append(Spacer(1, 0.3*cm))

    # ============== SECTION 1: SUMMARY ==============
    story.append(PageBreak())
    story.append(Paragraph(T['sec_summary'], h1))

    total_km = sum(summaries[d]['distance_km'] for d in dates)
    total_min = sum(summaries[d]['duration_min'] for d in dates)
    total_asc = sum((summaries[d].get('ascent_m') or 0) for d in dates)
    h_total = int(total_min // 60)
    m_total = int(total_min % 60)
    story.append(Paragraph(
        T['summary_intro'].format(n=n_sessions, km=total_km, h=h_total, m=m_total, asc=int(total_asc)),
        body
    ))

    # Summary table
    sum_header = [T['col_date'], T['col_dist'], T['col_dur'], T['col_avg_hr'],
                  T['col_avg_pwr'], T['col_np'], T['col_tss'], T['col_te']]
    sum_data = [sum_header]
    for d in dates:
        s = summaries[d]
        sum_data.append([
            d[8:10]+'/'+d[5:7],
            f"{s['distance_km']:.1f} km",
            f"{int(s['duration_min'])} min",
            f"{s['avg_hr']} bpm" if s.get('avg_hr') else '—',
            f"{s['avg_power']} W" if s.get('avg_power') else '—',
            f"{s['np']} W" if s.get('np') else '—',
            f"{s['tss']:.1f}" if s.get('tss') else '—',
            f"{s['training_effect']:.1f}" if s.get('training_effect') else '—',
        ])
    sum_tbl = Table(sum_data, colWidths=[2*cm, 1.9*cm, 1.7*cm, 1.7*cm, 2.2*cm, 1.7*cm, 1.5*cm, 1.5*cm])
    sum_tbl.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), PRIMARY),
        ('TEXTCOLOR',  (0,0), (-1,0), colors.white),
        ('FONTNAME',   (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE',   (0,0), (-1,-1), 9),
        ('ALIGN',      (0,0), (-1,-1), 'CENTER'),
        ('GRID',       (0,0), (-1,-1), 0.4, colors.grey),
        ('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white, LIGHT]),
        ('VALIGN',     (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('BOTTOMPADDING',(0,0),(-1,-1),5),
    ]))
    story.append(sum_tbl)
    story.append(Spacer(1, 0.4*cm))

    # Key findings - generated dynamically
    story.append(Paragraph(T['findings_title'], h3))
    findings = _generate_findings(summaries, context, lang)
    for f in findings:
        story.append(Paragraph(f"• {f}", bullet))

    # Cardiac alert if drift or recovery issues found
    if _has_cardiac_issues(summaries):
        story.append(Spacer(1, 0.3*cm))
        story.append(Paragraph(T['cardiac_alert'], body))

    # ============== SECTION 2: PER-SESSION ==============
    story.append(PageBreak())
    story.append(Paragraph(T['sec_per_session'], h1))

    sections = [
        ('sec_2_1', 'distance_duration', 'caption_1'),
        ('sec_2_2', 'heartrate',         'caption_2'),
        ('sec_2_2', 'hr_traces',         'caption_3'),
        ('sec_2_3', 'power',             'caption_4'),
        ('sec_2_3', 'power_traces',      'caption_5'),
        ('sec_2_4', 'tss_te',            'caption_6'),
        ('sec_2_5', 'hr_zones',          'caption_7'),
        ('sec_2_6', 'pwr_zones',         'caption_8'),
        ('sec_2_7', 'power_curve',       'caption_9'),
        ('sec_2_8', 'speed_cadence',     'caption_10'),
        ('sec_2_9', 'elevation',         'caption_11'),
    ]
    last_header = None
    for header_key, chart_key, cap_key in sections:
        chart_path = charts.get(chart_key)
        if not chart_path or not os.path.exists(chart_path):
            continue
        if header_key != last_header:
            story.append(Paragraph(T[header_key], h2))
            last_header = header_key
        # Read image size and scale to width
        story.append(Image(chart_path, width=16*cm, height=8*cm, kind='proportional'))
        cap = T[cap_key]
        if '{ftp}' in cap:
            cap = cap.format(ftp=context['ftp'])
        story.append(Paragraph(cap, caption))

    # ============== SECTION 3: RECOMMENDATIONS ==============
    story.append(PageBreak())
    story.append(Paragraph(T['sec_reco'], h1))
    story.append(Paragraph(T['reco_intro'], body))

    # Adapt for medical context
    medical = (profile.get('medical_notes') or '').lower()
    has_diabetes = any(k in medical for k in ['diabet', 'diabetes', 'dm', 'gula darah tinggi'])

    story.append(Paragraph(T['sec_3_1'], h2))
    for title, desc in T['priorities']:
        # If diabetes is in notes, modify priority 2 (VO2 max intervals) to be more cautious
        if has_diabetes and title.startswith('2.'):
            if lang == 'id':
                desc = '<b>(Disesuaikan untuk profil medis):</b> Tunda interval VO2 Max intensitas tinggi sampai mendapat izin dokter dan gula darah terkontrol. Fokus dulu pada Zona 2 endurance dan strength training, yang justru sangat efektif menurunkan resistensi insulin.'
            else:
                desc = '<b>(Adapted for medical profile):</b> Hold off on high-intensity VO2 Max intervals until physician clearance and glucose is controlled. Focus first on Zone 2 endurance and strength training, which are highly effective at lowering insulin resistance.'
        story.append(Paragraph(f"<b>{title}</b>", h3))
        story.append(Paragraph(desc, body))

    story.append(Paragraph(T['sec_3_2'], h2))
    week_data = [T['week_header']] + list(T['week_rows'])
    week_tbl = Table(week_data, colWidths=[2*cm, 5.5*cm, 2*cm, 4.5*cm, 2.2*cm])
    week_tbl.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), PRIMARY),
        ('TEXTCOLOR',  (0,0), (-1,0), colors.white),
        ('FONTNAME',   (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE',   (0,0), (-1,-1), 9),
        ('ALIGN',      (0,0), (-1,-1), 'CENTER'),
        ('ALIGN',      (1,1), (1,-1), 'LEFT'),
        ('GRID',       (0,0), (-1,-1), 0.4, colors.grey),
        ('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white, LIGHT]),
        ('VALIGN',     (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('BOTTOMPADDING',(0,0),(-1,-1),5),
    ]))
    story.append(week_tbl)
    story.append(Spacer(1, 0.2*cm))
    story.append(Paragraph(T['week_note'], body))

    story.append(Paragraph(T['sec_3_3'], h2))
    for item in T['recovery_items']:
        story.append(Paragraph(f"• {item}", bullet))

    story.append(Paragraph(T['sec_3_4'], h2))
    target_rows = _build_target_table(summaries, context, profile, T, lang)
    target_tbl = Table(target_rows, colWidths=[4.5*cm, 4*cm, 4*cm, 4*cm])
    target_tbl.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), PRIMARY),
        ('TEXTCOLOR',  (0,0), (-1,0), colors.white),
        ('FONTNAME',   (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE',   (0,0), (-1,-1), 9),
        ('ALIGN',      (0,0), (-1,-1), 'CENTER'),
        ('ALIGN',      (0,1), (0,-1), 'LEFT'),
        ('GRID',       (0,0), (-1,-1), 0.4, colors.grey),
        ('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white, LIGHT]),
        ('FONTNAME',   (0,1), (0,-1), 'Helvetica-Bold'),
        ('VALIGN',     (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING',(0,0),(-1,-1),6),
    ]))
    story.append(target_tbl)

    story.append(Paragraph(T['sec_3_5'], h2))
    for item in T['measure_items']:
        story.append(Paragraph(f"• {item}", bullet))

    story.append(Paragraph(T['sec_3_6'], h2))
    story.append(Paragraph(T['notes_med'], body))
    story.append(Paragraph(T['notes_progress'], body))
    story.append(Paragraph(T['notes_climate'], body))

    story.append(Spacer(1, 1*cm))
    story.append(Paragraph(T['footer'], small))

    doc.build(story)
    return output_path


# ----------------------------------------------------------------------
# Helpers for dynamic content
# ----------------------------------------------------------------------

def _generate_findings(summaries, context, lang):
    """Generate 4-6 key findings dynamically based on data."""
    findings = []
    dates = sorted(summaries.keys())

    # Best session (highest TSS)
    tss_dates = [(d, summaries[d].get('tss') or 0) for d in dates]
    tss_dates.sort(key=lambda x: x[1], reverse=True)
    if tss_dates and tss_dates[0][1] > 0:
        best = tss_dates[0]
        s = summaries[best[0]]
        if lang == 'id':
            findings.append(f"Sesi terkeras: <b>{best[0]}</b> — {s['distance_km']:.1f} km, TSS {best[1]:.0f}, Training Effect {s.get('training_effect', '?')}.")
        else:
            findings.append(f"Hardest session: <b>{best[0]}</b> — {s['distance_km']:.1f} km, TSS {best[1]:.0f}, Training Effect {s.get('training_effect', '?')}.")

    # Cadence issue
    cads = [summaries[d].get('avg_cadence') for d in dates if summaries[d].get('avg_cadence')]
    if cads:
        avg_cad = sum(cads) / len(cads)
        if avg_cad < 80:
            if lang == 'id':
                findings.append(f"<b>Cadence rata-rata {avg_cad:.0f} rpm rendah</b> (optimal 85–95). Memperbaiki cadence saja bisa menambah 10–15% pada power.")
            else:
                findings.append(f"<b>Average cadence {avg_cad:.0f} rpm is low</b> (optimal 85–95). Just fixing cadence can add 10–15% power.")

    # Power-to-weight
    npws = [summaries[d].get('np_w_per_kg') for d in dates if summaries[d].get('np_w_per_kg')]
    if npws:
        best_np = max(npws)
        if lang == 'id':
            level = 'rekreasi' if best_np < 2.0 else ('Cat 5' if best_np < 2.5 else 'Cat 4+')
            findings.append(f"Power-to-weight terbaik (NP): {best_np:.2f} W/kg — level {level}.")
        else:
            level = 'recreational' if best_np < 2.0 else ('Cat 5' if best_np < 2.5 else 'Cat 4+')
            findings.append(f"Best power-to-weight (NP): {best_np:.2f} W/kg — {level} level.")

    # Z1 dominance check
    high_z1 = []
    for d in dates:
        zs = summaries[d].get('pwr_zone_seconds') or {}
        total = sum(zs.values())
        if total > 0:
            z1_pct = (zs.get('Z1', 0) / total) * 100
            if z1_pct > 50:
                high_z1.append((d, z1_pct))
    if len(high_z1) >= len(dates) * 0.5 and high_z1:
        avg_z1 = sum(p for _, p in high_z1) / len(high_z1)
        if lang == 'id':
            findings.append(f"Sebagian besar waktu ({avg_z1:.0f}% rata-rata) dihabiskan di Zona Power 1 (Recovery) — perlu latihan terstruktur untuk merangsang adaptasi.")
        else:
            findings.append(f"Most time (avg {avg_z1:.0f}%) spent in Power Zone 1 (Recovery) — structured training needed to stimulate adaptation.")

    # Cardiac drift
    if _has_cardiac_issues(summaries):
        if lang == 'id':
            findings.append("Terdeteksi <b>cardiac drift &gt;10 bpm</b> di satu atau lebih sesi (HR naik meski power tidak naik) — sering tanda dehidrasi, heat stress, atau kelelahan.")
        else:
            findings.append("<b>Cardiac drift &gt;10 bpm</b> detected in one or more sessions (HR climbing despite stable power) — often signals dehydration, heat stress, or fatigue.")

    return findings


def _has_cardiac_issues(summaries):
    for d in summaries:
        drifts = summaries[d].get('cardiac_drift') or []
        for entry in drifts:
            if abs(entry.get('drift_bpm', 0)) > 10:
                return True
        rec = summaries[d].get('hr_recovery_coast') or {}
        if rec and rec.get('mean_drop_30s') is not None and rec['mean_drop_30s'] < 5:
            return True
    return False


def _build_target_table(summaries, context, profile, T, lang):
    """Build the 3-/6-month target table dynamically based on current data."""
    ftp = context['ftp']
    w = profile['weight_kg']
    age = profile.get('age', 40)
    vo2 = profile.get('vo2max_cycling', 35.0)

    # Get current bests
    dates = sorted(summaries.keys())
    p5min_now = max((summaries[d].get('p5min') or 0) for d in dates) if dates else 0
    p1min_now = max((summaries[d].get('p1min') or 0) for d in dates) if dates else 0
    cads = [summaries[d].get('avg_cadence') for d in dates if summaries[d].get('avg_cadence')]
    cad_now = int(sum(cads) / len(cads)) if cads else 75

    rows = [T['target_header']]
    if lang == 'id':
        rows.append(['FTP', f'{ftp} W ({ftp/w:.2f} W/kg)', f'{int(ftp*1.15)} W (+15%)', f'{int(ftp*1.30)} W (+30%)'])
        rows.append(['VO2 Max (Cycling)', f'{vo2} ml/kg/min', f'{vo2+3:.0f} ml/kg/min', f'{vo2+6:.0f} ml/kg/min'])
        if p5min_now:
            rows.append(['Power 5 menit', f'{p5min_now} W', f'{int(p5min_now*1.20)} W', f'{int(p5min_now*1.40)} W'])
        if p1min_now:
            rows.append(['Power 1 menit', f'{p1min_now} W', f'{int(p1min_now*1.15)} W', f'{int(p1min_now*1.30)} W'])
        rows.append(['Cadence rata-rata', f'{cad_now} rpm', f'{min(cad_now+10, 90)} rpm', '88-92 rpm'])
        rows.append(['Berat badan (opsional)', f'{w} kg', f'{w-3} kg', f'{w-5} kg'])
    else:
        rows.append(['FTP', f'{ftp} W ({ftp/w:.2f} W/kg)', f'{int(ftp*1.15)} W (+15%)', f'{int(ftp*1.30)} W (+30%)'])
        rows.append(['VO2 Max (Cycling)', f'{vo2} ml/kg/min', f'{vo2+3:.0f} ml/kg/min', f'{vo2+6:.0f} ml/kg/min'])
        if p5min_now:
            rows.append(['5-min Power', f'{p5min_now} W', f'{int(p5min_now*1.20)} W', f'{int(p5min_now*1.40)} W'])
        if p1min_now:
            rows.append(['1-min Power', f'{p1min_now} W', f'{int(p1min_now*1.15)} W', f'{int(p1min_now*1.30)} W'])
        rows.append(['Avg Cadence', f'{cad_now} rpm', f'{min(cad_now+10, 90)} rpm', '88-92 rpm'])
        rows.append(['Body Weight (optional)', f'{w} kg', f'{w-3} kg', f'{w-5} kg'])
    return rows
