import streamlit as st
import requests
import pandas as pd
import plotly.express as px

# ===========================
# Konfigurasi Halaman
# ===========================
st.set_page_config(page_title="AI POS Insight Dashboard", page_icon="🤖", layout="wide")
st.title("🤖 AI POS Insight - Fraud Detection Dashboard")
st.markdown("Masukkan data transaksi untuk mendeteksi **potensi kecurangan (fraud)** secara otomatis.")

# ===========================
# Inisialisasi Data Riwayat
# ===========================
if "history" not in st.session_state:
    st.session_state.history = pd.DataFrame(columns=["Total", "Item", "Diskon", "Score", "Status"])

# ===========================
# Input Data
# ===========================
with st.container():
    col1, col2, col3 = st.columns(3)
    with col1:
        total_amount = st.number_input("💰 Total Transaksi (Rp)", min_value=10000, value=500000)
    with col2:
        item_count = st.number_input("📦 Jumlah Item", min_value=1, value=3)
    with col3:
        discount = st.slider("🏷️ Diskon (%)", 0, 80, 10)

# ===========================
# Analisis dengan API
# ===========================
if st.button("🔍 Analisis Transaksi"):
    url = "http://127.0.0.1:8000/analyze"
    data = {
        "total_amount": total_amount,
        "item_count": item_count,
        "discount": discount
    }

    try:
        response = requests.post(url, json=data)
        result = response.json()

        if "fraud_status" in result:
            fraud_score = result["fraud_score"]
            fraud_status = result["fraud_status"]

            # Tambahkan ke riwayat
            new_data = pd.DataFrame([{
                "Total": total_amount,
                "Item": item_count,
                "Diskon": discount,
                "Score": round(fraud_score, 3),
                "Status": fraud_status
            }])
            st.session_state.history = pd.concat([st.session_state.history, new_data], ignore_index=True)

            # Tampilkan hasil
            if fraud_status == "POTENSI FRAUD":
                st.error(f"⚠️ {fraud_status} (Score: {fraud_score})")
            else:
                st.success(f"✅ {fraud_status} (Score: {fraud_score})")
        else:
            st.warning("⚠️ Tidak ada respon dari API.")
    except Exception as e:
        st.error(f"Terjadi kesalahan: {e}")

# ===========================
# Tampilkan Riwayat & Grafik
# ===========================
if not st.session_state.history.empty:
    st.markdown("---")
    st.subheader("📋 Riwayat Analisis Transaksi")

    # Tampilkan tabel riwayat
    st.dataframe(st.session_state.history, use_container_width=True)

    # Hitung statistik
    fraud_count = (st.session_state.history["Status"] == "POTENSI FRAUD").sum()
    normal_count = (st.session_state.history["Status"] == "NORMAL").sum()
    total_count = len(st.session_state.history)

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Transaksi Dianalisis", total_count)
    col2.metric("Potensi Fraud", fraud_count)
    col3.metric("Normal", normal_count)

    # Tampilkan pie chart
    st.subheader("📊 Proporsi Transaksi NORMAL vs FRAUD")
    fig = px.pie(
        st.session_state.history,
        names="Status",
        title="Distribusi Hasil Analisis",
        color="Status",
        color_discrete_map={"NORMAL": "green", "POTENSI FRAUD": "red"}
    )
    st.plotly_chart(fig, use_container_width=True)

else:
    st.info("Belum ada transaksi yang dianalisis. Masukkan data untuk memulai 🚀")

st.markdown("---")
st.caption("Ditenagai oleh AI POS Insight 🚀")
