import joblib

# Muat model dan scaler
model = joblib.load("fraud_model.pkl")
scaler = joblib.load("scaler.pkl")

print("✅ Model dan Scaler berhasil dimuat.")
