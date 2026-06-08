# 📊 Báo Cáo So Sánh Hiệu Năng Các Mô Hình

Báo cáo này tự động đánh giá và so sánh sai số dự báo **1 giờ tiếp theo (1-Hour Ahead)** của các mô hình trên tập kiểm thử chung.

### 📌 Chỉ số: water_pH (không đơn vị)

| Mô hình | RMSE ↓ | MAE ↓ | R² Score (%) ↑ |
| :--- | :---: | :---: | :---: |
| **GRU** | 0.5183 | 0.3528 | 95.52% |
| **LSTM** | 0.6240 | 0.4353 | 93.51% |
| **SEQ2SEQ** | 0.7443 | 0.4362 | 90.91% |
| **XGBOOST** | 0.9743 | 0.5211 | 84.18% |

---

### 📌 Chỉ số: TDS (ppm)

| Mô hình | RMSE ↓ | MAE ↓ | R² Score (%) ↑ |
| :--- | :---: | :---: | :---: |
| **XGBOOST** | 36.0145 ppm | 24.6909 ppm | 71.14% |
| **GRU** | 37.0143 ppm | 24.3671 ppm | 69.52% |
| **LSTM** | 43.6879 ppm | 33.1827 ppm | 57.54% |
| **SEQ2SEQ** | 50.5560 ppm | 39.3889 ppm | 39.53% |

---

### 📌 Chỉ số: water_temp (°C)

| Mô hình | RMSE ↓ | MAE ↓ | R² Score (%) ↑ |
| :--- | :---: | :---: | :---: |
| **XGBOOST** | 0.1268 °C | 0.0871 °C | 97.03% |
| **GRU** | 0.1386 °C | 0.1058 °C | 96.45% |
| **LSTM** | 0.1666 °C | 0.1246 °C | 94.86% |
| **SEQ2SEQ** | 0.2816 °C | 0.2167 °C | 85.27% |

---

