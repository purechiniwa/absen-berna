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
def get_dropdown_options(query):
    try:
        conn = create_connection()
        cursor = conn.cursor()
        cursor.execute(query)
        results = cursor.fetchall()
        cursor.close()
        conn.close()
        return [row[0] for row in results]
    except Error as e:
        st.error(f"Dropdown fetch error: {e}")
        return []

# ---------- Streamlit Page Config ----------
st.set_page_config(page_title="Absensi Entry", layout="centered")
st.title("📋 Absensi Form ")

# ---------- Load Dropdown Lists ----------
nama_list = get_dropdown_options("SELECT nama_lengkap FROM data_sensus")
event_list = get_dropdown_options("SELECT event_id FROM event")

# ---------- Absensi Form ----------
st.subheader("✍️ Input Absensi")
with st.form("absensi_form"):
    nama_lengkap = st.selectbox("👤 Nama Lengkap", nama_list)
    event_id = st.text_input("📌 Event ID")  # Changed from selectbox to text_input

    submitted = st.form_submit_button("✅ Submit Absensi")

    if submitted:
        try:
            jakarta = pytz.timezone("Asia/Jakarta")
            date_come = datetime.now(jakarta)
            conn = create_connection()
            cursor = conn.cursor()

            # --- Fetch start and end time for the entered event_id ---
            cursor.execute("""
                SELECT date_start, date_end 
                FROM event 
                WHERE event_id = %s
            """, (event_id,))
            result = cursor.fetchone()

            if result:
                date_start, date_end = result
                # Check if current time is within the event period
                if date_start.tzinfo is None:
                    date_start = jakarta.localize(date_start)
                if date_end.tzinfo is None:
                    date_end = jakarta.localize(date_end)
                if date_start <= date_come <= date_end:
                    cursor.execute("""
                        INSERT INTO absensi (nama_lengkap, event_id, date_come)
                        VALUES (%s, %s, %s)
                    """, (nama_lengkap, event_id, date_come.strftime("%Y-%m-%d %H:%M:%S")))
                    conn.commit()
                    st.success(f"✔️ Absensi berhasil untuk **{nama_lengkap}** pada `{date_come}`")
                else:
                    st.warning(f"⛔ Waktu absensi di luar rentang event.\n\nEvent dimulai `{date_start}` dan berakhir `{date_end}`.")
            else:
                st.error("❌ Event ID tidak ditemukan.")

            cursor.close()
            conn.close()

        except Error as e:

            st.error(f"❌ Insert error: {e}")


