# Sơ đồ Tuần tự (Sequence Diagrams)
## Hệ thống Giám sát và Điều khiển Môi trường Nuôi trồng Thủy sản IoT

---

## Danh sách các chức năng chính

| STT | Chức năng | Mô tả |
|-----|-----------|-------|
| SD-01 | Nhận và lưu dữ liệu cảm biến | ESP32 gửi dữ liệu qua MQTT, backend lưu vào DB |
| SD-02 | Điều khiển thiết bị (ON/OFF) | Người dùng gửi lệnh qua API, backend publish MQTT |
| SD-03 | Xem dữ liệu cảm biến mới nhất | Dashboard truy vấn giá trị hiện tại của thiết bị |
| SD-04 | Xem lịch sử cảm biến | Dashboard truy vấn time-series theo loại chỉ số |
| SD-05 | Xem danh sách thiết bị | Dashboard lấy toàn bộ danh sách thiết bị |
| SD-06 | Kết nối MQTT khi khởi động | Backend khởi động và thiết lập kết nối MQTT |
| SD-07 | Tự động kết nối lại MQTT | Xử lý mất kết nối và reconnect tự động |

---

## SD-01: Nhận và lưu dữ liệu cảm biến

**Mô tả:** ESP32 định kỳ đo các chỉ số môi trường và gửi lên MQTT Broker. Backend lắng nghe, parse dữ liệu và lưu vào cơ sở dữ liệu.

```mermaid
sequenceDiagram
    participant ESP32 as ESP32<br/>(Sensor Node)
    participant Broker as MQTT Broker<br/>(Mosquitto)
    participant MQTT as MQTT Client<br/>(Backend Thread)
    participant SVC as Sensor Service
    participant DEV as Device Service
    participant DB as MySQL Database

    ESP32->>Broker: PUBLISH sensor/esp32_1/temperature<br/>{"value": 28.5, "unit": "C"}

    Broker->>MQTT: on_message callback<br/>topic="sensor/esp32_1/temperature"

    Note over MQTT: Parse topic:<br/>device_id = "esp32_1"<br/>metric_type = "temperature"

    Note over MQTT: Parse payload:<br/>value = 28.5, unit = "C"

    MQTT->>MQTT: asyncio.run_coroutine_threadsafe()<br/>chuyển sang async event loop

    par Lưu dữ liệu cảm biến
        MQTT->>SVC: save_sensor_data(device_id, metric_type, value, unit)
        SVC->>DB: INSERT INTO sensor_data<br/>(device_id, metric_type, value, unit, created_at)
        DB-->>SVC: OK (id = 42)
        SVC-->>MQTT: SensorData object
    and Cập nhật last_seen
        MQTT->>DEV: update_last_seen(device_id)
        DEV->>DB: UPDATE devices SET last_seen = NOW()<br/>WHERE device_id = 'esp32_1'
        DB-->>DEV: OK (1 row affected)
        DEV-->>MQTT: Done
    end

    MQTT->>DB: COMMIT transaction
    Note over MQTT: Ghi log: "Saved temperature=28.5 for esp32_1"
```

**Luồng xử lý chính:**
1. ESP32 publish message lên topic `sensor/{device_id}/{metric_type}`
2. MQTT Broker forward message đến tất cả subscriber
3. Backend nhận qua callback `on_message` (chạy trên paho thread)
4. Dùng `asyncio.run_coroutine_threadsafe` để gọi async DB service từ sync thread
5. Thực hiện song song: INSERT sensor_data + UPDATE devices.last_seen
6. Commit transaction

---

## SD-02: Điều khiển thiết bị

**Mô tả:** Người dùng gửi lệnh điều khiển qua REST API. Backend publish lệnh qua MQTT đến thiết bị, cập nhật trạng thái và ghi log.

```mermaid
sequenceDiagram
    participant User as Người dùng<br/>(Dashboard)
    participant API as FastAPI<br/>(devices router)
    participant DEV as Device Service
    participant DB as MySQL Database
    participant MQTT as MQTT Client
    participant Broker as MQTT Broker<br/>(Mosquitto)
    participant ESP32 as Thiết bị<br/>(ESP32/Pump)

    User->>API: POST /devices/PUMP_OXY_01/control<br/>{"action": "ON"}

    API->>DEV: get_device_by_id("PUMP_OXY_01")
    DEV->>DB: SELECT * FROM devices<br/>WHERE device_id = 'PUMP_OXY_01'
    DB-->>DEV: Device object

    alt Thiết bị không tồn tại
        DEV-->>API: None
        API-->>User: 404 Not Found<br/>{"detail": "Device not found"}
    else Thiết bị tồn tại
        DEV-->>API: Device object

        API->>MQTT: publish("control/PUMP_OXY_01", {"action": "ON"})
        MQTT->>Broker: PUBLISH control/PUMP_OXY_01<br/>{"action": "ON"}
        Broker->>ESP32: on_message: {"action": "ON"}
        Note over ESP32: Thực thi lệnh:<br/>Bật máy bơm

        API->>DEV: update_device_status("PUMP_OXY_01", "ON")
        DEV->>DB: UPDATE devices SET status = 'ON'<br/>WHERE device_id = 'PUMP_OXY_01'
        DB-->>DEV: OK

        API->>DEV: log_device_history(device_id, action, "success", "api")
        DEV->>DB: INSERT INTO device_history<br/>(device_id, action, status, source, note)
        DB-->>DEV: OK

        API->>DB: COMMIT
        API-->>User: 200 OK<br/>{"device_id": "PUMP_OXY_01", "action": "ON",<br/>"status": "success", "message": "..."}
    end
```

**Lưu ý:**
- Chỉ cập nhật `devices.status` khi action là `ON` hoặc `OFF`
- Các action `FEED`, `RESET`, `CHANGE_WATER` chỉ publish MQTT và ghi log, không đổi status
- Nếu publish MQTT thất bại, vẫn ghi log với `status = 'failed'`

---

## SD-03: Xem dữ liệu cảm biến mới nhất

**Mô tả:** Dashboard lấy giá trị đo lường mới nhất của từng loại chỉ số cho một thiết bị cụ thể.

```mermaid
sequenceDiagram
    participant User as Người dùng<br/>(Dashboard)
    participant API as FastAPI<br/>(sensors router)
    participant SVC as Sensor Service
    participant DB as MySQL Database

    User->>API: GET /sensors/latest?device_id=esp32_1

    API->>SVC: get_latest_by_device("esp32_1")

    SVC->>DB: SELECT s.* FROM sensor_data s<br/>INNER JOIN (<br/>  SELECT metric_type, MAX(created_at) AS max_time<br/>  FROM sensor_data<br/>  WHERE device_id = 'esp32_1'<br/>  GROUP BY metric_type<br/>) latest ON s.metric_type = latest.metric_type<br/>       AND s.created_at = latest.max_time<br/>WHERE s.device_id = 'esp32_1'

    Note over DB: Sử dụng index:<br/>idx_device_time (device_id, created_at)

    DB-->>SVC: [SensorData × N metric types]

    SVC-->>API: List[SensorData]

    API-->>User: 200 OK<br/>[<br/>  {"metric_type": "temperature", "value": 28.5, "unit": "C", ...},<br/>  {"metric_type": "ph", "value": 7.2, "unit": "pH", ...},<br/>  {"metric_type": "o2", "value": 6.8, "unit": "mg/L", ...}<br/>]
```

**Kỹ thuật query:**
Dùng subquery với `GROUP BY metric_type` + `MAX(created_at)` để lấy đúng 1 bản ghi mới nhất cho mỗi loại chỉ số, tránh N+1 query.

---

## SD-04: Xem lịch sử cảm biến (Time-series)

**Mô tả:** Dashboard lấy chuỗi dữ liệu lịch sử của một loại chỉ số để vẽ biểu đồ.

```mermaid
sequenceDiagram
    participant User as Người dùng<br/>(Dashboard)
    participant API as FastAPI<br/>(sensors router)
    participant SVC as Sensor Service
    participant DB as MySQL Database

    User->>API: GET /sensors/history?metric_type=temperature&limit=100

    Note over API: Validate params:<br/>metric_type required<br/>limit: 1-1000, default 100

    API->>SVC: get_history_by_metric("temperature", limit=100)

    SVC->>DB: SELECT * FROM sensor_data<br/>WHERE metric_type = 'temperature'<br/>ORDER BY created_at DESC<br/>LIMIT 100

    Note over DB: Sử dụng index:<br/>idx_metric_time (metric_type, created_at)

    DB-->>SVC: [SensorData × 100 rows]

    SVC-->>API: List[SensorData]

    API-->>User: 200 OK<br/>[<br/>  {"id": 42, "device_id": "esp32_1", "metric_type": "temperature",<br/>   "value": 28.5, "unit": "C", "created_at": "2024-01-15T10:30:00"},<br/>  {"id": 41, "device_id": "esp32_1", "metric_type": "temperature",<br/>   "value": 28.3, "unit": "C", "created_at": "2024-01-15T10:25:00"},<br/>  ...<br/>]
```

---

## SD-05: Xem danh sách thiết bị

**Mô tả:** Dashboard lấy toàn bộ danh sách thiết bị kèm trạng thái hiện tại.

```mermaid
sequenceDiagram
    participant User as Người dùng<br/>(Dashboard)
    participant API as FastAPI<br/>(devices router)
    participant SVC as Device Service
    participant DB as MySQL Database

    User->>API: GET /devices

    API->>SVC: get_all_devices()

    SVC->>DB: SELECT * FROM devices<br/>ORDER BY created_at ASC

    DB-->>SVC: [Device × N rows]

    SVC-->>API: List[Device]

    API-->>User: 200 OK<br/>[<br/>  {"id": 1, "device_id": "esp32_1", "name": "Cảm biến ao A",<br/>   "type": "esp32", "status": "ON", "last_seen": "2024-01-15T10:30:00", ...},<br/>  {"id": 2, "device_id": "PUMP_OXY_01", "name": "Máy bơm oxy",<br/>   "type": "pump", "status": "OFF", "last_seen": "2024-01-15T09:00:00", ...}<br/>]

    Note over User: Dashboard hiển thị:<br/>- Thiết bị online/offline (dựa vào last_seen)<br/>- Trạng thái ON/OFF hiện tại
```

---

## SD-06: Khởi động hệ thống và kết nối MQTT

**Mô tả:** Quá trình khởi động backend — khởi tạo DB và thiết lập kết nối MQTT.

```mermaid
sequenceDiagram
    participant Docker as Docker Compose
    participant App as FastAPI App<br/>(main.py)
    participant DB as MySQL Database
    participant MQTT as MQTT Client
    participant Broker as MQTT Broker<br/>(Mosquitto)

    Docker->>App: docker-compose up --build
    Note over Docker: Chờ mysql healthy<br/>Chờ mqtt started

    App->>App: startup() event triggered

    App->>DB: init_db() — create_all(tables)
    Note over DB: Tạo bảng nếu chưa tồn tại:<br/>devices, sensor_data, device_history
    DB-->>App: Tables ready

    App->>MQTT: set_event_loop(asyncio.get_running_loop())
    Note over MQTT: Lưu reference đến async loop<br/>để dùng trong paho thread

    App->>MQTT: connect()
    MQTT->>Broker: TCP connect to mqtt:1883
    Broker-->>MQTT: CONNACK (rc=0, success)

    MQTT->>Broker: SUBSCRIBE sensor/+/+ (QoS=1)
    Broker-->>MQTT: SUBACK

    Note over MQTT: loop_start()<br/>Background thread bắt đầu lắng nghe

    App->>App: logger.info("Backend started successfully")
    App-->>Docker: Application startup complete

    Note over App: Sẵn sàng nhận request tại<br/>http://0.0.0.0:8000
```

---

## SD-07: Tự động kết nối lại MQTT (Reconnect)

**Mô tả:** Khi mất kết nối đến MQTT Broker, hệ thống tự động thử kết nối lại sau 5 giây, tối đa 10 lần.

```mermaid
sequenceDiagram
    participant Broker as MQTT Broker<br/>(Mosquitto)
    participant MQTT as MQTT Client<br/>(Backend)
    participant Timer as Reconnect Timer<br/>(threading.Timer)

    Note over Broker,MQTT: Kết nối đang hoạt động bình thường...

    Broker->>MQTT: Connection lost (network error)
    MQTT->>MQTT: on_disconnect(rc != 0)
    Note over MQTT: connected = False<br/>reconnect_count = 0

    MQTT->>Timer: threading.Timer(5s, _do_reconnect)
    Timer->>Timer: sleep 5 seconds

    loop Thử kết nối lại (tối đa 10 lần)
        Timer->>MQTT: _do_reconnect()
        MQTT->>Broker: reconnect()

        alt Kết nối thành công
            Broker-->>MQTT: CONNACK (rc=0)
            MQTT->>MQTT: on_connect: connected=True<br/>reconnect_count = 0
            MQTT->>Broker: SUBSCRIBE sensor/+/+ (QoS=1)
            Note over MQTT: Hoạt động bình thường trở lại
        else Kết nối thất bại
            Broker-->>MQTT: Connection refused / timeout
            MQTT->>MQTT: on_disconnect(rc != 0)<br/>reconnect_count += 1

            alt reconnect_count < 10
                MQTT->>Timer: threading.Timer(5s, _do_reconnect)
                Note over Timer: Thử lại sau 5 giây
            else reconnect_count >= 10
                MQTT->>MQTT: logger.error("Max retries reached")
                Note over MQTT: Dừng thử kết nối lại<br/>Cần can thiệp thủ công
            end
        end
    end
```

---

## Tổng hợp các thành phần tham gia

```
┌─────────────┐    ┌──────────────┐    ┌─────────────────┐    ┌──────────────┐
│    ESP32    │    │ MQTT Broker  │    │  FastAPI Backend │    │    MySQL     │
│ Sensor Node │    │  Mosquitto   │    │                  │    │  Database    │
└──────┬──────┘    └──────┬───────┘    └────────┬─────────┘    └──────┬───────┘
       │                  │                     │                     │
       │  SD-01: Gửi data │                     │                     │
       │─────────────────►│                     │                     │
       │                  │────────────────────►│                     │
       │                  │                     │────────────────────►│
       │                  │                     │                     │
       │                  │◄────────────────────│  SD-02: Nhận lệnh   │
       │◄─────────────────│                     │                     │
       │                  │                     │────────────────────►│
       │                  │                     │                     │
       │                  │         SD-03/04/05: Query data           │
       │                  │                     │◄────────────────────│
       │                  │                     │                     │
```

| Thành phần | Vai trò | Giao thức |
|------------|---------|-----------|
| **ESP32** | Thu thập và gửi dữ liệu cảm biến | MQTT (publish) |
| **MQTT Broker** | Trung gian nhận/phân phối message | MQTT |
| **FastAPI Backend** | Xử lý logic nghiệp vụ, REST API | HTTP/MQTT |
| **MySQL Database** | Lưu trữ dữ liệu bền vững | SQL/TCP |
| **Dashboard** | Giao diện người dùng | HTTP REST |
