# Sơ đồ Use Case - Hệ thống Giám sát Nuôi trồng Thủy sản IoT

## Actors

| Actor | Mô tả |
|-------|-------|
| **Người dùng (Dashboard)** | Operator/admin tương tác qua REST API hoặc giao diện web |
| **Thiết bị ESP32** | Sensor node gửi dữ liệu môi trường qua MQTT |
| **MQTT Broker** | Eclipse Mosquitto — trung gian nhận/phân phối message |

---

## Sơ đồ

```mermaid
graph TB
    subgraph Actors
        User(["👤 Người dùng\nDashboard"])
        ESP32(["🔌 Thiết bị ESP32\nSensor Node"])
        MQTT(["📡 MQTT Broker\nMosquitto"])
    end

    subgraph Backend["IoT Aquaculture Backend"]

        subgraph DeviceMgmt["📦 Quản lý Thiết bị"]
            UC01["UC01 · Xem danh sách thiết bị"]
            UC02["UC02 · Xem chi tiết thiết bị"]
            UC03["UC03 · Điều khiển thiết bị\nON / OFF / FEED / RESET / CHANGE_WATER"]
            UC04["UC04 · Cập nhật trạng thái thiết bị"]
            UC05["UC05 · Ghi lịch sử hành động"]
        end

        subgraph SensorData["📊 Dữ liệu Cảm biến"]
            UC06["UC06 · Nhận dữ liệu cảm biến qua MQTT"]
            UC07["UC07 · Lưu dữ liệu cảm biến vào DB"]
            UC08["UC08 · Xem dữ liệu mới nhất theo thiết bị"]
            UC09["UC09 · Xem lịch sử theo metric type"]
            UC10["UC10 · Cập nhật last_seen thiết bị"]
        end

        subgraph System["⚙️ Hệ thống"]
            UC11["UC11 · Health check"]
            UC12["UC12 · Publish lệnh điều khiển qua MQTT"]
            UC13["UC13 · Tự động reconnect MQTT"]
        end
    end

    %% User interactions
    User -->|GET /devices| UC01
    User -->|GET /devices/:id| UC02
    User -->|POST /devices/:id/control| UC03
    User -->|GET /sensors/latest| UC08
    User -->|GET /sensors/history| UC09
    User -->|GET /health| UC11

    %% ESP32 → MQTT → Backend
    ESP32 -->|publish sensor/+/+| MQTT
    MQTT -->|forward| UC06

    %% UC03 includes
    UC03 -->|include| UC04
    UC03 -->|include| UC05
    UC03 -->|include| UC12

    %% UC06 includes
    UC06 -->|include| UC07
    UC06 -->|include| UC10

    %% MQTT publish back to device
    UC12 -->|publish control/device_id| MQTT
    MQTT -->|subscribe control/+| ESP32

    %% Reconnect
    UC13 -.->|extend| UC06
```

---

## Mô tả Use Cases

### Quản lý Thiết bị

| UC | Tên | Actor | Mô tả |
|----|-----|-------|-------|
| UC01 | Xem danh sách thiết bị | Người dùng | `GET /devices` — trả về tất cả thiết bị đã đăng ký |
| UC02 | Xem chi tiết thiết bị | Người dùng | `GET /devices/{device_id}` — trả về thông tin 1 thiết bị |
| UC03 | Điều khiển thiết bị | Người dùng | `POST /devices/{device_id}/control` — gửi lệnh ON/OFF/FEED/RESET/CHANGE_WATER |
| UC04 | Cập nhật trạng thái | System | **include** UC03 — cập nhật `devices.status` khi action là ON/OFF |
| UC05 | Ghi lịch sử hành động | System | **include** UC03 — insert vào `device_history` với source=api |

### Dữ liệu Cảm biến

| UC | Tên | Actor | Mô tả |
|----|-----|-------|-------|
| UC06 | Nhận dữ liệu MQTT | MQTT Broker | Subscribe `sensor/+/+`, parse topic → device_id + metric_type |
| UC07 | Lưu vào DB | System | **include** UC06 — insert vào `sensor_data` |
| UC08 | Xem dữ liệu mới nhất | Người dùng | `GET /sensors/latest?device_id=` — giá trị mới nhất mỗi metric |
| UC09 | Xem lịch sử metric | Người dùng | `GET /sensors/history?metric_type=` — time series data |
| UC10 | Cập nhật last_seen | System | **include** UC06 — cập nhật `devices.last_seen` |

### Hệ thống

| UC | Tên | Actor | Mô tả |
|----|-----|-------|-------|
| UC11 | Health check | Người dùng | `GET /health` — kiểm tra backend đang chạy |
| UC12 | Publish MQTT command | System | **include** UC03 — publish `{"action": "ON"}` tới `control/{device_id}` |
| UC13 | Auto reconnect MQTT | System | **extend** UC06 — tự kết nối lại khi mất kết nối broker |

---

## Luồng chính: Điều khiển thiết bị (UC03)

```
Người dùng
    │
    ▼
POST /devices/esp32_1/control  {"action": "ON"}
    │
    ├─► [UC12] Publish MQTT → control/esp32_1  {"action": "ON"}
    │       │
    │       └─► ESP32 nhận lệnh, thực thi
    │
    ├─► [UC04] UPDATE devices SET status='ON' WHERE device_id='esp32_1'
    │
    └─► [UC05] INSERT device_history (action=ON, status=success, source=api)
```

## Luồng chính: Nhận dữ liệu cảm biến (UC06)

```
ESP32
    │
    ▼
MQTT publish → sensor/esp32_1/temperature  {"value": 28.5, "unit": "C"}
    │
    ▼
MQTT Broker (Mosquitto)
    │
    ▼
Backend on_message callback
    │
    ├─► [UC07] INSERT sensor_data (device_id=esp32_1, metric_type=temperature, value=28.5)
    │
    └─► [UC10] UPDATE devices SET last_seen=NOW() WHERE device_id='esp32_1'
```
