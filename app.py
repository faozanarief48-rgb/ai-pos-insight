from fastapi import FastAPI
from pydantic import BaseModel
import joblib
import numpy as np

# =============================
# Inisialisasi FastAPI
# =============================
app = FastAPI()

# =============================
# Muat model dan scaler
# =============================
model = joblib.load("fraud_model.pkl")
scaler = joblib.load("scaler.pkl")

# =============================
# Struktur input data
# =============================
class Transaction(BaseModel):
    total_amount: float
    item_count: int
    discount: float

# =============================
# Endpoint utama
# =============================
@app.post("/analyze")
def analyze(transaction: Transaction):
    data = np.array([[transaction.total_amount, transaction.item_count, transaction.discount]])
    data_scaled = scaler.transform(data)
    fraud_score = model.predict_proba(data_scaled)[0][1]

    fraud_status = "POTENSI FRAUD" if (fraud_score > 0.75 or transaction.discount > 40) else "NORMAL"

    return {
        "fraud_score": float(fraud_score),
        "fraud_status": fraud_status
    }
