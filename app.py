import streamlit as st
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import calendar
from ics import Calendar as IcsCalendar, Event
from datetime import datetime, timedelta
import pytz

# --- KONFIGURASI HALAMAN ---
st.set_page_config(page_title="Family Shift Sync (Final Text Fix)", layout="wide")

# --- DATABASE LIBUR 2026 ---
HOLIDAYS = {
    (1, 1): "TAHUN BARU",
    (1, 16): "ISRA MI'RAJ",
    (2, 17): "IMLEK",          
    (3, 19): "NYEPI",
    (3, 20): "CUTI BERSAMA",   
    (3, 21): "IDUL FITRI",      
    (3, 22): "IDUL FITRI",
    (3, 31): "PASKAH",          
    (4, 3):  "WAFAT ISA ALMASIH", 
    (5, 1): "HARI BURUH",
    (5, 14): "KENAIKAN ISA",
    (5, 27): "IDUL ADHA",        
    (5, 31): "WAISAK",
    (6, 1): "PANCASILA",
    (6, 16): "1 MUHARRAM",      
    (8, 17): "KEMERDEKAAN",
    (8, 25): "MAULID NABI",      
    (12, 25): "NATAL"
}

# --- WARNA ---
C_HEADER = '#1e5f9e'
C_DAY_HEADER = '#4a8bc2'
C_WORKDAY = '#ffffff'
C_LEAVE = '#e8f5e9'     # HIJAU MUDA (Istri Libur)
C_HIGHLIGHT = '#c62828' # Merah
C_TERAPI = '#1565c0'    # Biru
C_GROOMING = '#2e7d32'  # Hijau Tua
C_TIME = '#ef6c00'      # ORANYE
C_HOLIDAY_BG = '#ffcdd2'

# --- FUNGSI LOGIKA STATUS ---
def get_status(day, month, year, shift_istri, prev_shift):
    holiday_name = HOLIDAYS.get((month, day))

    # Logika Sekolah (Libur Semester & Tanggal Merah)
    school_active = True
    if month == 1 and day < 5: school_active = False
    if month == 6 and day > 20: school_active = False 
    if month == 7 and day < 15: school_active = False 
    if month == 12 and day > 20: school_active = False 
    if holiday_name: school_active = False

    wife_home = True if shift_istri == "Libur" else False
    is_post_night = True if prev_shift == "Malam" else False

    return {
        "holiday_name": holiday_name,
        "school_active": school_active,
        "wife_home": wife_home,
        "shift": shift_istri,
        "is_post_night": is_post_night
    }

# --- FUNGSI GENERATE ALARM (ICS FILE) ---
def generate_ics_file(year, month, shifts):
    c = IcsCalendar()
    num_days = calendar.monthrange(year, month)[1]
    wib = pytz.timezone("Asia/Jakarta")

    for d in range(1, num_days + 1):
        prev_s = "Pagi"
        if d > 1: prev_s = shifts[d-1]

        stt = get_status(d, month, year, shifts[d], prev_s)
        current_date = datetime(year, month, d)
        weekday = current_date.weekday()

        # LOGIKA ALARM
        if not stt['wife_home']:
            pickup_time = None
            note = ""

            # Jika Tanggal Merah & Istri Kerja -> Libur total
            if stt['holiday_name']:
                pass

            # SABTU
            elif weekday == 5:
                if stt['shift'] == "Malam" and not stt['is_post_night']:
                    pass # Siang Aman
                else:
                    pickup_time = "14:30"
                    note = "⚠️ PENITIPAN TUTUP 15.00!"

            # SENIN-JUMAT (Bukan Libur)
            elif weekday <= 4:
                 if stt['shift'] == "Siang":
                     pickup_time = "16:30"
                     note = "Istri Shift Siang"

            if pickup_time:
                e = Event()
                e.name = f"🚗 JEMPUT HANA ({pickup_time})"
                h, m = map(int, pickup_time.split(':'))
                start_dt = datetime(year, month, d, h, m)
                e.begin = wib.localize(start_dt)
                e.duration = timedelta(minutes=30)
                e.description = f"{note} - Jadwal Otomatis Family App"
                e.alarms = [timedelta(minutes=-30)]
                c.events.add(e)

        # Alarm Sabtu Malam Kedua (Terapi)
        if weekday == 5 and stt['shift'] == "Malam" and stt['is_post_night']:
            e = Event()
            e.name = "🏥 TERAPI + ANTAR HANA (09.30)"
            start_dt = datetime(year, month, d, 9, 30)
            e.begin = wib.localize(start_dt)
            e.duration = timedelta(hours=1)
            e.description = "Istri Post-Night (Tidur). Bawa HANA sekalian."
            e.alarms = [timedelta(minutes=-30)]
            c.events.add(e)

        # Alarm Post Night Weekday
        if weekday <= 4 and stt['is_post_night'] and stt['school_active']:
            e = Event()
            e.name = "🏫 ANTAR 2 ANAK (07.00)"
            start_dt = datetime(year, month, d, 7, 0)
            e.begin = wib.localize(start_dt)
            e.duration = timedelta(minutes=30)
            e.description = "Istri Post-Night. Antar Abang & HANA."
            e.alarms = [timedelta(minutes=-15)]
            c.events.add(e)

    return c.serialize()

# --- FUNGSI GAMBAR KALENDER (VISUAL) ---
def draw_calendar(year, month, shifts):
    cal_obj = calendar.Calendar(firstweekday=6)
    month_days = cal_obj.monthdayscalendar(year, month)
    n_weeks = len(month_days)

    fig, ax = plt.subplots(figsize=(12, 16), dpi=100)
    ax.set_axis_off()

    month_name = calendar.month_name[month].upper()
    plt.text(0.5, 0.98, f"JADWAL {month_name} {year}", ha='center', va='center', fontsize=28, weight='bold', color=C_HEADER)

    days_header = ['MINGGU', 'SENIN', 'SELASA', 'RABU', 'KAMIS', 'JUMAT', 'SABTU']
    col_width = 1.0 / 7
    start_y = 0.92
    row_height = (start_y - 0.02) / n_weeks

    for i, day in enumerate(days_header):
        rect = patches.Rectangle((i * col_width, start_y), col_width, 0.03, facecolor=C_DAY_HEADER, edgecolor='white')
        ax.add_patch(rect)
        plt.text(i * col_width + col_width/2, start_y + 0.015, day, ha='center', va='center', color='white', fontsize=10, weight='bold')

    y_pos = start_y
    for week in month_days:
        y_pos -= row_height
        for col_idx, d in enumerate(week):
            x_pos = col_idx * col_width

            if d == 0: continue

            prev_s = "Pagi"
            if d > 1: prev_s = shifts[d-1]

            stt = get_status(d, month, year, shifts[d], prev_s)

            # --- LOGIKA BACKGROUND COLOR ---
            bg_color = C_WORKDAY
            if stt['wife_home']: bg_color = C_LEAVE
            if col_idx == 0: bg_color = '#ffebee' # Minggu
            if stt['holiday_name']: bg_color = C_HOLIDAY_BG # Tanggal Merah
            
            danger_sunday = (col_idx == 0 and (not stt['wife_home'] or stt['is_post_night']))

            rect = patches.Rectangle((x_pos, y_pos), col_width, row_height, facecolor=bg_color, edgecolor='#b0bec5', linewidth=1)
            ax.add_patch(rect)

            t_color = C_HEADER
            if col_idx == 0 or stt['holiday_name']: t_color = C_HIGHLIGHT
            plt.text(x_pos + col_width - 0.015, y_pos + row_height - 0.02, str(d), ha='right', va='top', fontsize=16, weight='bold', color=t_color)

            # --- FUNGSI TULIS TEKS ---
            def w(text, line, color='#000', size=7.5, weight='normal'):
                spacing = 0.0135
                top_margin = 0.06
                yt = y_pos + row_height - top_margin - (line * spacing)
                plt.text(x_pos + 0.015, yt, text, ha='left', va='top', fontsize=size, color=color, weight=weight)

            # ==========================================
            # 1. TANGGAL MERAH (LOGIC SHIFT MALAM)
            # ==========================================
            if stt['holiday_name']:
                w(stt['holiday_name'], 0, color=C_HIGHLIGHT, weight='bold', size=8)
                w("(LIBUR)", 1, color=C_HIGHLIGHT, weight='bold')

                # Logika: Start Shift Malam = Siang Masih di Rumah
                is_night_shift_start = (stt['shift'] == "Malam" and not stt['is_post_night'])

                if stt['wife_home']:
                     w("(Istri Libur)", 2.5, color='#555', size=7)
                     w("GROOMING", 3.5, color=C_GROOMING, weight='bold')
                
                elif is_night_shift_start:
                     w(f"(Istri {stt['shift']})", 2.5, color='#555', size=7)
                     w("SIANG AMAN", 3.5, color=C_GROOMING, weight='bold', size=7)
                     w("GROOMING", 4.3, color=C_GROOMING, weight='bold')
                
                else:
                     w(f"(Istri {stt['shift']})", 2.5, color='#555', size=7)
                     w("JAGA ANAK", 3.5, color='red', size=10, weight='bold')
                     w("PENITIPAN TUTUP", 4.5, color='red', size=7)
                
                continue 

            # 2. MINGGU
            if col_idx == 0:
                if danger_sunday:
                    rect_h = patches.Rectangle((x_pos, y_pos), col_width, row_height, facecolor='#ffcdd2', edgecolor='red', linewidth=2)
                    ax.add_patch(rect_h)
                    plt.text(x_pos + 0.5*col_width, y_pos + 0.6*row_height, "PENITIPAN\nTUTUP!", ha='center', va='center', fontsize=9, color='red', weight='bold')
                    plt.text(x_pos + 0.5*col_width, y_pos + 0.4*row_height, "JAGA ANAK", ha='center', va='center', fontsize=11, color='red', weight='bold')

                    reason = f"(Istri {stt['shift']})"
                    if stt['is_post_night']: reason = "(Istri Plg Malam)"
                    plt.text(x_pos + 0.5*col_width, y_pos + 0.25*row_height, reason, ha='center', va='center', fontsize=7, color='#555')
                else:
                    w("LIBUR KELUARGA", 0, color=C_HIGHLIGHT, weight='bold')
                continue

            # 3. SENIN - KAMIS
            if 1 <= col_idx <= 4:
                if stt['is_post_night'] and stt['school_active']:
                     # REVISI WAKTU SEKOLAH: 07.00 - 09.20
                     w("07.00 - 09.20", 0, weight='bold', color='red')
                     w("ANTAR 2 ANAK", 1, size=7.5, weight='bold', color='red')
                     w("(Istri Plg Pagi)", 1.8, size=6.5, color='#555')
                elif stt['school_active']:
                    # REVISI WAKTU SEKOLAH: 07.00 - 09.20
                    w("07.00 - 09.20", 0, weight='bold', color=C_TIME)
                    w("Abang Sekolah", 1, size=7.5)
                else:
                    w("LIBUR SEKOLAH", 0, color='#e67e22', weight='bold', size=8)

                line_start = 2.5
                if stt['wife_home']:
                    w("(Istri Libur)", line_start, color='#555', size=7)
                    w("GROOMING", line_start+1, color=C_GROOMING, weight='bold')
                elif stt['shift'] == "Malam":
                    w("(Istri Malam)", line_start, color='#555', size=7)
                    if not stt['is_post_night']:
                        w("HANA DI RUMAH", line_start+1, color=C_GROOMING, weight='bold', size=7)
                        w("09.30", line_start+2, color=C_TIME, weight='bold', size=7)
                        w("GROOMING", line_start+2.8, color=C_GROOMING, weight='bold', size=7)
                    else:
                        w("09.30", line_start+1, color=C_TIME, weight='bold')
                        w("GROOMING", line_start+1.8, color=C_GROOMING, weight='bold')
                elif stt['shift'] == "Siang":
                    w(f"(Istri {stt['shift']})", line_start, color='#555', size=7)
                    w("09.30", line_start+1, color=C_TIME, weight='bold', size=7)
                    w("GROOMING", line_start+1.8, color=C_GROOMING, weight='bold', size=7)
                    # REVISI TEKS JMPT -> JEMPUT
                    w("16.30 JEMPUT HANA", 5.5, color='red', weight='bold', size=7)
                else:
                    w(f"(Istri {stt['shift']})", line_start, color='#555', size=7)
                    w("09.30", line_start+1, color=C_TIME, weight='bold')
                    w("GROOMING", line_start+1.8, color=C_GROOMING, weight='bold')

            # 4. JUMAT
            elif col_idx == 5:
                if stt['school_active']:
                    if stt['is_post_night']:
                         w("07.00 ANTAR 2", 0, weight='bold', color='red')
                    else:
                         # REVISI WAKTU JUMAT: 07.00 - 08.50
                         w("07.00 - 08.50", 0, weight='bold', color=C_TIME)
                    w("Abang Sekolah", 0.9, size=7)

                    wife_status = f"(Istri {stt['shift']})"
                    if stt['wife_home']: wife_status = "(Istri Libur)"
                    w(wife_status, 1.7, color='#555', size=7)

                    if stt['shift'] == "Malam" and not stt['is_post_night']:
                        w("HANA DI RUMAH", 2.8, color=C_GROOMING, weight='bold', size=7)
                    else:
                        w("09.00 - 12.00", 2.8, weight='bold', color=C_TIME)
                        w("GROOMING", 3.7, size=7, color=C_GROOMING, weight='bold')

                    w("12.30 - 14.30", 5.0, weight='bold', color=C_TIME)
                    w("TERAPI", 5.9, size=7, color=C_TERAPI, weight='bold')

                    if stt['shift'] == "Siang":
                        # REVISI TEKS JMPT -> JEMPUT
                        w("16.30 JEMPUT HANA", 7.5, weight='bold', color='red', size=7)
                    else:
                        w("15.00 - 17.00", 7.2, weight='bold', color=C_TIME)
                        w("GROOMING", 8.1, size=7, color=C_GROOMING, weight='bold')
                else:
                    w("LIBUR SEKOLAH", 0, color='#e67e22', weight='bold', size=8)
                    wife_status = f"(Istri {stt['shift']})"
                    if stt['wife_home']: wife_status = "(Istri Libur)"
                    w(wife_status, 1.5, color='#555', size=7)
                    w("12.30", 3, color=C_TIME, weight='bold')
                    w("TERAPI", 3.8, color=C_TERAPI, weight='bold')
                    if stt['shift'] == "Siang":
                         # REVISI TEKS JMPT -> JEMPUT
                         w("16.30 JEMPUT HANA", 7.5, weight='bold', color='red', size=7)
                    else:
                         w("GROOMING", 5.2, color=C_GROOMING, weight='bold')

            # 5. SABTU
            elif col_idx == 6:
                offset = 0
                status_txt = f"(Istri {stt['shift']})"
                if stt['is_post_night']: status_txt = "(Istri Plg Pagi)"
                if stt['wife_home']: status_txt = "(Istri Libur)"
                w(status_txt, 0, size=7, color='#555')

                if stt['shift'] == "Malam" and stt['is_post_night']:
                    w("09.30", 1.0, color='red', weight='bold')
                    w("TERAPI + ANTAR HANA", 1.8, color='red', weight='bold', size=6.5)
                else:
                    w("09.30", 1.0, color=C_TIME, weight='bold')
                    w("TERAPI", 1.8, color=C_TERAPI, weight='bold')

                w("12.00", 3.0, color=C_TIME, weight='bold')
                w("GROOMING", 3.8, color=C_GROOMING, weight='bold')

                if not stt['wife_home']:
                    if stt['shift'] == "Malam" and not stt['is_post_night']:
                        w("HANA DI RUMAH", 5.2, color=C_GROOMING, weight='bold', size=7)
                    else:
                        # REVISI TEKS JMPT -> JEMPUT
                        w("14.30 JEMPUT HANA", 5.2, color='red', weight='bold', size=7)

    return fig

# --- TAMPILAN APLIKASI ---
st.title("📅 Aplikasi Jadwal Keluarga 2.0")

# --- PERBAIKAN TAMPILAN PC ---
col_left, col_right = st.columns([1, 1])

with col_left:
    st.header("1. Input Shift")

    nama_bulan = list(calendar.month_name)[1:]
    map_bulan = {
        "Januari": 1, "Februari": 2, "Maret": 3, "April": 4, "Mei": 5, "Juni": 6,
        "Juli": 7, "Agustus": 8, "September": 9, "Oktober": 10, "November": 11, "Desember": 12
    }

    bulan_pilihan = st.selectbox("Pilih Bulan (2026)", list(map_bulan.keys()), index=0)
    month_int = map_bulan[bulan_pilihan]

    num_days = calendar.monthrange(2026, month_int)[1]
    user_shifts = {}

    with st.form("input_shift"):
        st.write(f"**Shift Istri ({bulan_pilihan} 2026):**")
        cols = None
        for d in range(1, num_days + 1):
            if (d - 1) % 3 == 0:
                cols = st.columns(3)
            col = cols[(d - 1) % 3]

            def_idx = 0
            if month_int == 1 and (d <= 17 or d == 24 or d == 30):
                def_idx = 3

            col.write(f"**Tgl {d}**")
            val = col.selectbox(f"shift_{d}", ["Pagi", "Siang", "Malam", "Libur"], index=def_idx, key=d, label_visibility="collapsed")
            user_shifts[d] = val

        submitted = st.form_submit_button("🔄 GENERATE JADWAL", type="primary")

with col_right:
    if submitted:
        st.header("2. Hasil Kalender & Alarm")

        # 1. Gambar Kalender Visual
        fig = draw_calendar(2026, month_int, user_shifts)
        st.pyplot(fig)

        # Tombol Download Gambar
        col_dl1, col_dl2 = st.columns(2)
        fn_img = f"Jadwal_{bulan_pilihan}_2026.png"
        plt.savefig(fn_img, bbox_inches='tight', dpi=200)
        with open(fn_img, "rb") as img:
            col_dl1.download_button("📥 Download Gambar", img, fn_img, "image/png")

        # 2. GENERATE ALARM (.ICS)
        ics_data = generate_ics_file(2026, month_int, user_shifts)
        fn_ics = f"Alarm_Jadwal_{bulan_pilihan}_2026.ics"
        col_dl2.download_button(
            label="⏰ Download Alarm (Kalender HP)",
            data=ics_data,
            file_name=fn_ics,
            mime="text/calendar"
        )
        st.caption("ℹ️ Cara Pakai Alarm: Klik tombol 'Download Alarm', buka file-nya di HP, lalu pilih 'Add All to Calendar'. HP akan otomatis bunyi 30 menit sebelum jadwal Jemput/Antar!")

    else:
        st.info("Klik tombol GENERATE untuk melihat jadwal.")
