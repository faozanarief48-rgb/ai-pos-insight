import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier
import joblib

# ==============================
# 1️⃣ Buat data contoh transaksi
# ==============================
np.random.seed(42)
n_samples = 200

data = pd.DataFrame({
    "total_amount": np.random.randint(10000, 10000000, n_samples),
    "item_count": np.random.randint(1, 10, n_samples),
    "discount": np.random.randint(0, 80, n_samples)
})

# ==============================
# 2️⃣ Tentukan logika FRAUD manual
# ==============================
# Logika: jika diskon > 40% maka potensi fraud
data["fraud"] = (data["discount"] > 40).astype(int)

# ==============================
# 3️⃣ Pisahkan fitur dan target
# ==============================
X = data[["total_amount", "item_count", "discount"]]
y = data["fraud"]

# ==============================
# 4️⃣ Normalisasi data
# ==============================
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

# ==============================
# 5️⃣ Latih model AI
# ==============================
model = RandomForestClassifier(n_estimators=100, random_state=42)
model.fit(X_scaled, y)

# ==============================
# 6️⃣ Simpan model dan scaler
# ==============================
joblib.dump(model, "fraud_model.pkl")
joblib.dump(scaler, "scaler.pkl")

print("✅ Model dan Scaler berhasil disimpan dengan aturan: diskon > 40% = POTENSI FRAUD")
