import streamlit as st
import mysql.connector
from mysql.connector import Error
from datetime import datetime
import pytz

# ---------- MySQL Connection via Secrets ----------
def create_connection():
    return mysql.connector.connect(
        host=st.secrets["mysql"]["host"],
        port=st.secrets["mysql"]["port"],
        user=st.secrets["mysql"]["user"],
        password=st.secrets["mysql"]["password"],
        database=st.secrets["mysql"]["database"],
        ssl_verify_cert=False,
        ssl_disabled=False
    )

# ---------- Fetch Dropdown Data ----------
def get_dropdown_options(query, params=None):
    try:
        conn = create_connection()
        cursor = conn.cursor()
        cursor.execute(query, params or ())
        results = cursor.fetchall()
        cursor.close()
        conn.close()
        return [row[0] for row in results]
    except Error as e:
        st.error(f"Dropdown fetch error: {e}")
        return []

# ---------- Streamlit Page Config ----------
st.set_page_config(page_title="Absensi Entry", layout="centered")
st.title("📋 Absensi Form")

# ---------- Load Dropdown Lists ----------
wilayah_list = get_dropdown_options("SELECT DISTINCT wilayah FROM data_sensus ORDER BY wilayah")
lingkungan_list = []
nama_list = []

# ---------- Step 1: Wilayah Selection ----------
st.subheader("🌍 Pilih Wilayah dan Lingkungan")
selected_wilayah = st.selectbox("🏘️ Wilayah", ["-- Pilih Wilayah --"] + wilayah_list)

if selected_wilayah != "-- Pilih Wilayah --":
    lingkungan_list = get_dropdown_options(
        "SELECT DISTINCT lingkungan FROM data_sensus WHERE wilayah = %s ORDER BY lingkungan",
        (selected_wilayah,)
    )

# ---------- Step 2: Lingkungan Selection ----------
selected_lingkungan = st.selectbox("🏡 Lingkungan", ["-- Pilih Lingkungan --"] + lingkungan_list)

if selected_lingkungan != "-- Pilih Lingkungan --":
    nama_list = get_dropdown_options(
        "SELECT nama_lengkap FROM data_sensus WHERE wilayah = %s AND lingkungan = %s ORDER BY nama_lengkap",
        (selected_wilayah, selected_lingkungan)
    )

# ---------- Step 3: Load Event List ----------
event_list = get_dropdown_options("SELECT event_code FROM event ORDER BY event_code")

# ---------- Absensi Form ----------
st.subheader("✍️ Input Absensi")
with st.form("absensi_form"):
    nama_lengkap = st.selectbox("👤 Nama Lengkap", nama_list if nama_list else ["-- Pilih Nama --"])
    event_code = st.text_input("📌 Event Code")

    submitted = st.form_submit_button("✅ Submit Absensi")

    if submitted:
        if not nama_list or nama_lengkap == "-- Pilih Nama --":
            st.warning("⚠️ Silakan pilih nama lengkap yang valid.")
        elif not event_code.strip():
            st.warning("⚠️ Masukkan kode event yang valid.")
        else:
            try:
                jakarta = pytz.timezone("Asia/Jakarta")
                date_come = datetime.now(jakarta)
                conn = create_connection()
                cursor = conn.cursor()

                # --- Fetch event time ---
                cursor.execute("""
                    SELECT date_start, date_end 
                    FROM event 
                    WHERE event_code = %s
                """, (event_code,))
                result = cursor.fetchone()

                if result:
                    date_start, date_end = result
                    if date_start.tzinfo is None:
                        date_start = jakarta.localize(date_start)
                    if date_end.tzinfo is None:
                        date_end = jakarta.localize(date_end)

                    # --- Format readable day/date/time ---
                    hari_dict = {
                        0: "Senin", 1: "Selasa", 2: "Rabu", 3: "Kamis",
                        4: "Jumat", 5: "Sabtu", 6: "Minggu"
                    }

                    bulan_dict = {
                        "January": "Januari", "February": "Februari", "March": "Maret",
                        "April": "April", "May": "Mei", "June": "Juni",
                        "July": "Juli", "August": "Agustus", "September": "September",
                        "October": "Oktober", "November": "November", "December": "Desember"
                    }

                    hari_start = hari_dict[date_start.weekday()]
                    hari_end = hari_dict[date_end.weekday()]

                    # translate month manually
                    bulan_start = bulan_dict[date_start.strftime("%B")]
                    bulan_end = bulan_dict[date_end.strftime("%B")]

                    tanggal_start = date_start.strftime(f"%d {bulan_start} %Y")
                    tanggal_end = date_end.strftime(f"%d {bulan_end} %Y")

                    jam_start = date_start.strftime("%H.%M")
                    jam_end = date_end.strftime("%H.%M")

                    # --- Absensi logic ---
                    if date_start <= date_come <= date_end:
                        initials = ''.join([n[0].upper() for n in nama_lengkap.split() if n])  # e.g. OBA
                        time_str = date_come.strftime("%H.%M")
                        special_code = f"{event_code}-{initials}-{time_str}"

                        cursor.execute("""
                            INSERT INTO absensi (nama_lengkap, event_code, date_come, special_code)
                            VALUES (%s, %s, %s, %s)
                        """, (nama_lengkap, event_code, date_come.strftime("%Y-%m-%d %H:%M:%S"), special_code))
                        conn.commit()

                        st.success(
                            f"✔️ Absensi berhasil untuk **{nama_lengkap}** pada `{date_come.strftime('%d %B %Y %H:%M')}`\n\n"
                            f"🆔 Kode Khusus: `{special_code}`"
                        )
                    else:
                        # --- Adjust message depending on same-day or multi-day event ---
                        if date_start.date() == date_end.date():
                            st.warning(
                                f"⛔ Waktu absensi di luar rentang event.\n\n"
                                f"📅 Event dimulai **{hari_start}, {tanggal_start} pukul {jam_start}** "
                                f"dan berakhir **{jam_end}**."
                            )
                        else:
                            st.warning(
                                f"⛔ Waktu absensi di luar rentang event.\n\n"
                                f"📅 Event dimulai **{hari_start}, {tanggal_start} pukul {jam_start}**\n"
                                f"🕓 dan berakhir **{hari_end}, {tanggal_end} pukul {jam_end}**."
                            )
                else:
                    st.error("❌ Event ID tidak ditemukan.")

                cursor.close()
                conn.close()

            except Error as e:
                st.error(f"❌ Insert error: {e}")

