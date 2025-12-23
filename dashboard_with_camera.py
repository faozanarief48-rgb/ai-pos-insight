import os
import sqlite3
from datetime import datetime
import joblib
import numpy as np
import pandas as pd
import streamlit as st
from io import BytesIO
import json
from google.oauth2.service_account import Credentials
import gspread

# ============================
# 🔧 KONFIGURASI STREAMLIT
# ============================
st.set_page_config(page_title="AI POS Insight", page_icon="🤖", layout="wide")
st.title("🤖 AI POS Insight - Fraud Detection Dashboard")

st.markdown("""
Selamat datang di **AI POS Insight**!  
Aplikasi ini menggunakan model AI untuk mendeteksi potensi *kecurangan transaksi (fraud)* secara otomatis,  
menyimpan hasil analisis ke **database lokal & Google Sheets**, serta mengambil **foto bukti** bila diperlukan.
""")

# ============================
# 🗃️ DATABASE SETUP
# ============================
conn = sqlite3.connect("fraud_records.db")
cursor = conn.cursor()
cursor.execute("""
CREATE TABLE IF NOT EXISTS fraud_transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    total REAL,
    item INTEGER,
    discount REAL,
    score REAL,
    status TEXT,
    photo_path TEXT,
    timestamp TEXT
)
""")
conn.commit()

# ============================
# 🧠 LOAD MODEL & SCALER
# ============================
model = joblib.load("fraud_model.pkl")
scaler = joblib.load("scaler.pkl")

# ============================
# 📥 INPUT DATA
# ============================
st.markdown("---")
st.subheader("💡 Masukkan Data Transaksi")
col1, col2, col3 = st.columns(3)
with col1:
    total_amount = st.number_input("💰 Total Transaksi (Rp)", min_value=10000, value=500000)
with col2:
    item_count = st.number_input("📦 Jumlah Item", min_value=1, value=3)
with col3:
    discount = st.slider("🏷️ Diskon (%)", 0, 80, 10)

# ============================
# 🔍 ANALISIS TRANSAKSI
# ============================
if st.button("🔍 Analisis Transaksi", key="analyze_main"):
    try:
        # Prediksi
        data = np.array([[total_amount, item_count, discount]])
        data_scaled = scaler.transform(data)
        fraud_score = model.predict_proba(data_scaled)[0][1]
        fraud_status = "POTENSI FRAUD" if fraud_score > 0.5 else "NORMAL"

        # Simpan ke database lokal
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute("""
            INSERT INTO fraud_transactions (total, item, discount, score, status, timestamp)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (total_amount, item_count, discount, float(fraud_score), fraud_status, timestamp))
        conn.commit()

        # Tampilkan hasil
        if fraud_status == "POTENSI FRAUD":
            st.error(f"⚠️ {fraud_status} (Score: {fraud_score:.2f})")
        else:
            st.success(f"✅ {fraud_status} (Score: {fraud_score:.2f})")

        # Simpan ke session state
        st.session_state.fraud_status = fraud_status
        st.session_state.timestamp = timestamp

        # ============================
        # ☁️ SIMPAN KE GOOGLE SHEETS
        # ============================
        try:
            scopes = ["https://www.googleapis.com/auth/spreadsheets"]
            creds_dict = json.loads(st.secrets["GOOGLE_SERVICE_ACCOUNT"])
            creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
            client = gspread.authorize(creds)

            SHEET_ID = "1L42saoykgtNDWP7pKAyo9BqI4_PKXpOOim-gyiSjnDM"
            SHEET_NAME = "Sheet1"
            sheet = client.open_by_key(SHEET_ID).worksheet(SHEET_NAME)

            sheet.append_row([
                total_amount,
                item_count,
                discount,
                float(fraud_score),
                fraud_status,
                timestamp
            ])
            st.success("✅ Data transaksi berhasil dikirim ke Google Sheets!")
        except Exception as e:
            st.warning(f"⚠️ Gagal mengirim data ke Google Sheets: {e}")

    except Exception as e:
        st.error(f"Terjadi kesalahan saat analisis: {e}")

# ============================
# 📸 KAMERA OTOMATIS
# ============================
if "fraud_status" in st.session_state and st.session_state.fraud_status == "POTENSI FRAUD":
    st.warning("⚠️ Transaksi mencurigakan! Silakan ambil foto bukti transaksi di bawah ini:")

    os.makedirs("fraud_photos", exist_ok=True)
    img = st.camera_input("📸 Ambil Foto Bukti Transaksi", key=f"fraud_camera_{st.session_state.timestamp}")

    if img is not None:
        img_bytes = img.getvalue()
        img_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_path = f"fraud_photos/fraud_{img_timestamp}.jpg"

        with open(file_path, "wb") as f:
            f.write(img_bytes)

        cursor.execute("""
            UPDATE fraud_transactions
            SET photo_path = ?
            WHERE timestamp = ?
        """, (file_path, st.session_state.timestamp))
        conn.commit()

        st.success(f"📷 Foto bukti tersimpan di: `{file_path}`")
        del st.session_state.fraud_status

# ============================
# 📋 RIWAYAT TRANSAKSI
# ============================
st.markdown("---")
st.header("📋 Riwayat Transaksi")

cursor.execute("SELECT total, item, discount, score, status, timestamp, photo_path FROM fraud_transactions ORDER BY id DESC")
records = cursor.fetchall()

if not records:
    st.info("Belum ada data transaksi.")
else:
    df = pd.DataFrame(records, columns=["Total (Rp)", "Item", "Diskon (%)", "Score", "Status", "Waktu", "Foto Bukti"])
    st.dataframe(df, width="stretch")

    # Tombol ekspor
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button("⬇️ Unduh CSV", csv, "fraud_transactions.csv", "text/csv")
