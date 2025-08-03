import streamlit as st
import mysql.connector
from mysql.connector import Error
from datetime import datetime

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
    event_id = st.selectbox("📌 Event ID", event_list)

    submitted = st.form_submit_button("✅ Submit Absensi")

    if submitted:
        try:
            date_come = datetime.now()
            conn = create_connection()
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO absensi (nama_lengkap, event_id, date_come)
                VALUES (%s, %s, %s)
            """, (nama_lengkap, event_id, date_come.strftime("%Y-%m-%d %H:%M:%S")))
            conn.commit()
            cursor.close()
            conn.close()
            st.success(f"✔️ Absensi telah berhasil **{nama_lengkap}** pada `{date_come}`")
        except Error as e:
            st.error(f"❌ Insert error: {e}")
