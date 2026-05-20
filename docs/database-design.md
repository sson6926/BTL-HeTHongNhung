# Thiết Kế Cơ Sở Dữ Liệu
## Hệ thống Giám sát và Điều khiển Môi trường Nuôi trồng Thủy sản IoT

---

## 1. Tổng quan

Hệ thống sử dụng **MySQL 8.0** làm hệ quản trị cơ sở dữ liệu quan hệ. Cơ sở dữ liệu được thiết kế để lưu trữ và quản lý ba loại thông tin chính:

1. **Thông tin thiết bị** — danh sách và trạng thái các thiết bị IoT trong hệ thống
2. **Dữ liệu cảm biến** — các chỉ số môi trường được thu thập liên tục từ thiết bị
3. **Lịch sử hành động** — nhật ký toàn bộ lệnh điều khiển đã được thực thi

Cơ sở dữ liệu gồm **3 bảng chính**, có quan hệ với nhau thông qua khóa ngoại.

---

## 2. Sơ đồ quan hệ thực thể (ERD)

```
┌─────────────────────────────────┐
│            devices              │
├─────────────────────────────────┤
│ PK  id          BIGINT          │
│ UQ  device_id   VARCHAR(50)     │◄──────────────┐
│     name        VARCHAR(100)    │               │
│     type        ENUM            │               │
│     status      ENUM            │               │
│     location    VARCHAR(100)    │               │
│     last_seen   TIMESTAMP       │               │
│     created_at  TIMESTAMP       │               │
│     updated_at  TIMESTAMP       │               │
└─────────────────────────────────┘               │
                                                  │ FK (device_id)
          ┌───────────────────────────────────────┤
          │                                       │
          ▼                                       ▼
┌──────────────────────────────┐   ┌──────────────────────────────────┐
│         sensor_data          │   │         device_history           │
├──────────────────────────────┤   ├──────────────────────────────────┤
│ PK  id          BIGINT       │   │ PK  id          BIGINT           │
│ FK  device_id   VARCHAR(50)  │   │ FK  device_id   VARCHAR(50)      │
│     metric_type VARCHAR(50)  │   │     action      ENUM             │
│     value       FLOAT        │   │     status      ENUM             │
│     unit        VARCHAR(20)  │   │     source      ENUM             │
│     created_at  TIMESTAMP    │   │     note        TEXT             │
└──────────────────────────────┘   │     created_at  TIMESTAMP        │
                                   └──────────────────────────────────┘
```

**Quan hệ:**
- `devices` (1) ←→ (N) `sensor_data` — một thiết bị có nhiều bản ghi cảm biến
- `devices` (1) ←→ (N) `device_history` — một thiết bị có nhiều bản ghi lịch sử
- Cả hai bảng con đều tham chiếu đến `devices.device_id` (không phải `devices.id`)

---

## 3. Mô tả chi tiết từng bảng

### 3.1. Bảng `devices` — Quản lý thiết bị

Bảng trung tâm của hệ thống, lưu trữ thông tin đăng ký và trạng thái hiện tại của tất cả thiết bị IoT.

```sql
CREATE TABLE devices (
    id         BIGINT AUTO_INCREMENT PRIMARY KEY,
    device_id  VARCHAR(50)  NOT NULL UNIQUE,
    name       VARCHAR(100) NOT NULL,
    type       ENUM('esp32', 'pump', 'feeder', 'relay') NOT NULL,
    status     ENUM('ON', 'OFF') DEFAULT 'OFF',
    location   VARCHAR(100),
    last_seen  TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);
```

#### Mô tả các cột

| Cột | Kiểu dữ liệu | Ràng buộc | Mô tả |
|-----|-------------|-----------|-------|
| `id` | BIGINT | PK, AUTO_INCREMENT | Khóa chính nội bộ, tự tăng. Dùng cho join giữa các bảng trong DB |
| `device_id` | VARCHAR(50) | NOT NULL, UNIQUE | **Định danh nghiệp vụ** của thiết bị (ví dụ: `ESP32_001`, `PUMP_OXY_01`). Đây là giá trị thiết bị tự khai báo trong firmware, được dùng trong MQTT topic và REST API |
| `name` | VARCHAR(100) | NOT NULL | Tên mô tả thân thiện, dễ đọc (ví dụ: "Cảm biến ao A", "Máy bơm oxy") |
| `type` | ENUM | NOT NULL | Phân loại thiết bị: `esp32` (vi điều khiển cảm biến), `pump` (máy bơm), `feeder` (máy cho ăn), `relay` (rơ-le điều khiển) |
| `status` | ENUM | DEFAULT 'OFF' | Trạng thái hiện tại của thiết bị. Được cập nhật mỗi khi nhận lệnh ON/OFF qua API |
| `location` | VARCHAR(100) | NULL | Vị trí vật lý của thiết bị (ví dụ: "Ao nuôi số 1", "Khu vực B") |
| `last_seen` | TIMESTAMP | NULL | Thời điểm cuối cùng thiết bị gửi dữ liệu lên hệ thống. Dùng để phát hiện thiết bị offline |
| `created_at` | TIMESTAMP | DEFAULT NOW() | Thời điểm thiết bị được đăng ký vào hệ thống |
| `updated_at` | TIMESTAMP | ON UPDATE NOW() | Tự động cập nhật mỗi khi bất kỳ cột nào trong bản ghi thay đổi |

#### Lý do thiết kế

- **Tại sao có cả `id` và `device_id`?** `id` là surrogate key (khóa thay thế) dùng nội bộ trong DB để join nhanh. `device_id` là natural key (khóa tự nhiên) do thiết bị tự định nghĩa — ESP32 không thể biết `id` của nó trong DB, nhưng nó biết tên của chính nó. Đây là pattern chuẩn trong hệ thống IoT.
- **Tại sao `last_seen` là NULL?** Khi thiết bị mới đăng ký nhưng chưa gửi dữ liệu lần nào, `last_seen` chưa có giá trị. NULL phân biệt rõ "chưa từng kết nối" với "đã kết nối lúc 00:00:00".
- **Tại sao dùng ENUM cho `type` và `status`?** Giới hạn tập giá trị hợp lệ ngay tại tầng DB, tránh dữ liệu rác. MySQL lưu ENUM hiệu quả hơn VARCHAR cho tập giá trị cố định.

---

### 3.2. Bảng `sensor_data` — Dữ liệu cảm biến

Bảng lưu trữ toàn bộ dữ liệu đo lường từ các cảm biến môi trường. Được thiết kế theo **Long Format** (định dạng dọc) — mỗi bản ghi chỉ chứa một chỉ số đo lường.

```sql
CREATE TABLE sensor_data (
    id          BIGINT AUTO_INCREMENT PRIMARY KEY,
    device_id   VARCHAR(50) NOT NULL,
    metric_type VARCHAR(50) NOT NULL,
    value       FLOAT       NOT NULL,
    unit        VARCHAR(20),
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_sensor_device
        FOREIGN KEY (device_id) REFERENCES devices(device_id)
        ON DELETE CASCADE,

    INDEX idx_device_time  (device_id, created_at),
    INDEX idx_metric_time  (metric_type, created_at)
);
```

#### Mô tả các cột

| Cột | Kiểu dữ liệu | Ràng buộc | Mô tả |
|-----|-------------|-----------|-------|
| `id` | BIGINT | PK, AUTO_INCREMENT | Khóa chính, định danh duy nhất mỗi bản ghi đo lường |
| `device_id` | VARCHAR(50) | FK → devices.device_id | Thiết bị đã gửi dữ liệu này. Tham chiếu đến `devices.device_id` |
| `metric_type` | VARCHAR(50) | NOT NULL | Loại chỉ số đo lường. Các giá trị trong hệ thống: `temperature`, `ph`, `nh3`, `o2`, `water_level`, `tds`, `turbidity` |
| `value` | FLOAT | NOT NULL | Giá trị số của chỉ số đo được |
| `unit` | VARCHAR(20) | NULL | Đơn vị đo lường tương ứng (ví dụ: `°C`, `pH`, `mg/L`, `cm`, `NTU`) |
| `created_at` | TIMESTAMP | DEFAULT NOW() | Thời điểm ghi nhận dữ liệu. Đây là trục thời gian cho time-series query |

#### Các chỉ số cảm biến trong hệ thống

| metric_type | Ý nghĩa | Đơn vị | Ngưỡng tham khảo |
|-------------|---------|--------|-----------------|
| `temperature` | Nhiệt độ nước | °C | 25 – 32°C |
| `ph` | Độ pH của nước | pH | 6.5 – 8.5 |
| `nh3` | Nồng độ amoniac | mg/L | < 0.1 mg/L |
| `o2` | Hàm lượng oxy hòa tan | mg/L | > 5 mg/L |
| `water_level` | Mực nước | cm | Tùy ao |
| `tds` | Tổng chất rắn hòa tan | ppm | 100 – 500 ppm |
| `turbidity` | Độ đục của nước | NTU | < 30 NTU |

#### Lý do chọn Long Format thay vì Wide Format

**Wide Format** (định dạng ngang — không dùng):
```
| device_id | temperature | ph  | nh3  | o2  | created_at          |
|-----------|-------------|-----|------|-----|---------------------|
| esp32_1   | 28.5        | 7.2 | 0.05 | 6.8 | 2024-01-15 10:30:00 |
```

**Long Format** (định dạng dọc — đang dùng):
```
| device_id | metric_type | value | unit | created_at          |
|-----------|-------------|-------|------|---------------------|
| esp32_1   | temperature | 28.5  | °C   | 2024-01-15 10:30:00 |
| esp32_1   | ph          | 7.2   | pH   | 2024-01-15 10:30:00 |
| esp32_1   | nh3         | 0.05  | mg/L | 2024-01-15 10:30:00 |
| esp32_1   | o2          | 6.8   | mg/L | 2024-01-15 10:30:00 |
```

Long Format được chọn vì:
1. **Linh hoạt mở rộng** — thêm loại cảm biến mới không cần ALTER TABLE
2. **Phù hợp với MQTT** — mỗi message MQTT chỉ mang một giá trị, ánh xạ trực tiếp thành một bản ghi
3. **Query time-series đơn giản** — `WHERE metric_type = 'temperature'` thay vì chọn cột động
4. **Không có giá trị NULL** — Wide Format sẽ có nhiều NULL khi các cảm biến không đồng bộ

#### Index và hiệu năng

Bảng `sensor_data` là bảng có tốc độ ghi cao nhất trong hệ thống (mỗi thiết bị gửi dữ liệu định kỳ). Hai composite index được tạo để tối ưu các truy vấn phổ biến:

| Index | Cột | Tối ưu cho query |
|-------|-----|-----------------|
| `idx_device_time` | `(device_id, created_at)` | `WHERE device_id = ? ORDER BY created_at DESC` — lấy lịch sử của một thiết bị |
| `idx_metric_time` | `(metric_type, created_at)` | `WHERE metric_type = ? ORDER BY created_at DESC` — lấy time-series theo loại chỉ số |

---

### 3.3. Bảng `device_history` — Lịch sử hành động

Bảng nhật ký (audit log) ghi lại toàn bộ các lệnh điều khiển đã được gửi đến thiết bị. Đây là bảng **append-only** — chỉ INSERT, không UPDATE hay DELETE.

```sql
CREATE TABLE device_history (
    id         BIGINT AUTO_INCREMENT PRIMARY KEY,
    device_id  VARCHAR(50) NOT NULL,
    action     ENUM('ON', 'OFF', 'FEED', 'RESET', 'CHANGE_WATER') NOT NULL,
    status     ENUM('success', 'failed') NOT NULL,
    source     ENUM('manual', 'api', 'schedule') NOT NULL,
    note       TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_history_device
        FOREIGN KEY (device_id) REFERENCES devices(device_id)
        ON DELETE CASCADE,

    INDEX idx_device_time (device_id, created_at)
);
```

#### Mô tả các cột

| Cột | Kiểu dữ liệu | Ràng buộc | Mô tả |
|-----|-------------|-----------|-------|
| `id` | BIGINT | PK, AUTO_INCREMENT | Khóa chính, định danh duy nhất mỗi bản ghi lịch sử |
| `device_id` | VARCHAR(50) | FK → devices.device_id | Thiết bị nhận lệnh điều khiển |
| `action` | ENUM | NOT NULL | Loại hành động được thực thi |
| `status` | ENUM | NOT NULL | Kết quả thực thi: `success` (thành công) hoặc `failed` (thất bại) |
| `source` | ENUM | NOT NULL | Nguồn phát sinh lệnh: `manual` (người dùng trực tiếp), `api` (qua REST API), `schedule` (lịch tự động) |
| `note` | TEXT | NULL | Ghi chú bổ sung, mô tả chi tiết hoặc thông báo lỗi nếu thất bại |
| `created_at` | TIMESTAMP | DEFAULT NOW() | Thời điểm lệnh được ghi nhận |

#### Các loại hành động (action)

| Giá trị | Mô tả | Thiết bị áp dụng |
|---------|-------|-----------------|
| `ON` | Bật thiết bị | pump, feeder, relay |
| `OFF` | Tắt thiết bị | pump, feeder, relay |
| `FEED` | Kích hoạt chu kỳ cho ăn | feeder |
| `RESET` | Khởi động lại thiết bị | esp32, relay |
| `CHANGE_WATER` | Kích hoạt quy trình thay nước | pump, relay |

#### Nguồn phát sinh lệnh (source)

| Giá trị | Mô tả |
|---------|-------|
| `manual` | Người vận hành thao tác trực tiếp trên thiết bị vật lý |
| `api` | Lệnh được gửi qua REST API (từ dashboard hoặc ứng dụng) |
| `schedule` | Lệnh được phát sinh tự động theo lịch đặt trước |

#### Lý do thiết kế

- **Tại sao lưu cả `status`?** Không phải lệnh nào cũng thành công (mất kết nối MQTT, thiết bị offline). Lưu `status` giúp phân tích tỷ lệ thành công và phát hiện sự cố.
- **Tại sao không UPDATE bảng này?** Đây là audit log — mọi sự kiện đều phải được bảo toàn nguyên vẹn để truy vết. Nếu cần sửa, ta thêm bản ghi mới thay vì sửa bản ghi cũ.
- **Tại sao có `note` kiểu TEXT?** Cho phép lưu thông báo lỗi chi tiết khi `status = 'failed'`, hỗ trợ debug mà không cần bảng log riêng.

---

## 4. Ràng buộc toàn vẹn dữ liệu

### 4.1. Khóa ngoại (Foreign Key)

| Bảng con | Cột FK | Bảng cha | Cột PK | ON DELETE |
|----------|--------|----------|--------|-----------|
| `sensor_data` | `device_id` | `devices` | `device_id` | CASCADE |
| `device_history` | `device_id` | `devices` | `device_id` | CASCADE |

**ON DELETE CASCADE** có nghĩa: khi một thiết bị bị xóa khỏi bảng `devices`, toàn bộ dữ liệu cảm biến và lịch sử liên quan cũng bị xóa theo. Điều này đảm bảo không có dữ liệu "mồ côi" (orphan records) trong DB.

### 4.2. Ràng buộc UNIQUE

- `devices.device_id` — đảm bảo không có hai thiết bị trùng định danh trong hệ thống

### 4.3. Ràng buộc NOT NULL

Các cột bắt buộc phải có giá trị:
- `devices`: `device_id`, `name`, `type`
- `sensor_data`: `device_id`, `metric_type`, `value`
- `device_history`: `device_id`, `action`, `status`, `source`

---

## 5. Chiến lược Index

Index là cấu trúc dữ liệu phụ giúp tăng tốc độ truy vấn. Hệ thống sử dụng **composite index** (index nhiều cột) thay vì single-column index vì các query thường lọc theo nhiều điều kiện cùng lúc.

### Phân tích các query phổ biến

**Query 1: Lấy dữ liệu mới nhất của một thiết bị**
```sql
SELECT * FROM sensor_data
WHERE device_id = 'esp32_1'
ORDER BY created_at DESC
LIMIT 1;
-- Sử dụng: idx_device_time (device_id, created_at)
```

**Query 2: Lấy time-series theo loại chỉ số**
```sql
SELECT * FROM sensor_data
WHERE metric_type = 'temperature'
ORDER BY created_at DESC
LIMIT 100;
-- Sử dụng: idx_metric_time (metric_type, created_at)
```

**Query 3: Lấy giá trị mới nhất mỗi metric của một thiết bị (subquery)**
```sql
SELECT s.*
FROM sensor_data s
INNER JOIN (
    SELECT metric_type, MAX(created_at) AS max_time
    FROM sensor_data
    WHERE device_id = 'esp32_1'
    GROUP BY metric_type
) latest ON s.metric_type = latest.metric_type
       AND s.created_at = latest.max_time
WHERE s.device_id = 'esp32_1';
-- Sử dụng: idx_device_time cho cả outer query và subquery
```

**Query 4: Lịch sử hành động của một thiết bị**
```sql
SELECT * FROM device_history
WHERE device_id = 'esp32_1'
ORDER BY created_at DESC;
-- Sử dụng: idx_device_time trong device_history
```

---

## 6. Sơ đồ luồng dữ liệu

```
ESP32 (Sensor Node)
        │
        │ MQTT publish
        │ Topic: sensor/esp32_1/temperature
        │ Payload: {"value": 28.5, "unit": "C"}
        ▼
MQTT Broker (Mosquitto)
        │
        │ on_message callback
        ▼
Backend (FastAPI)
        │
        ├──► INSERT INTO sensor_data
        │    (device_id='esp32_1', metric_type='temperature',
        │     value=28.5, unit='C', created_at=NOW())
        │
        └──► UPDATE devices
             SET last_seen = NOW()
             WHERE device_id = 'esp32_1'


Người dùng (Dashboard)
        │
        │ POST /devices/PUMP_OXY_01/control
        │ Body: {"action": "ON"}
        ▼
Backend (FastAPI)
        │
        ├──► MQTT publish
        │    Topic: control/PUMP_OXY_01
        │    Payload: {"action": "ON"}
        │
        ├──► UPDATE devices
        │    SET status = 'ON'
        │    WHERE device_id = 'PUMP_OXY_01'
        │
        └──► INSERT INTO device_history
             (device_id='PUMP_OXY_01', action='ON',
              status='success', source='api',
              note='Action ON triggered via REST API')
```

---

## 7. Ước tính dung lượng dữ liệu

Giả sử hệ thống có **10 thiết bị ESP32**, mỗi thiết bị gửi **7 loại chỉ số** mỗi **30 giây**:

| Thông số | Giá trị |
|----------|---------|
| Số bản ghi/phút | 10 × 7 × 2 = **140 bản ghi** |
| Số bản ghi/giờ | 140 × 60 = **8,400 bản ghi** |
| Số bản ghi/ngày | 8,400 × 24 = **201,600 bản ghi** |
| Số bản ghi/tháng | ~**6 triệu bản ghi** |
| Kích thước mỗi bản ghi | ~100 bytes |
| Dung lượng/tháng | ~**600 MB** |

**Khuyến nghị:** Với quy mô này, nên cân nhắc:
- Partition bảng `sensor_data` theo tháng (RANGE PARTITION trên `created_at`)
- Xây dựng job tự động xóa hoặc archive dữ liệu cũ hơn 6 tháng
- Tạo bảng aggregate lưu giá trị trung bình theo giờ để tăng tốc query dashboard

---

## 8. Script tạo cơ sở dữ liệu

```sql
-- Tạo database
CREATE DATABASE IF NOT EXISTS iot_db
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE iot_db;

-- Bảng devices
CREATE TABLE devices (
    id         BIGINT       AUTO_INCREMENT PRIMARY KEY,
    device_id  VARCHAR(50)  NOT NULL UNIQUE,
    name       VARCHAR(100) NOT NULL,
    type       ENUM('esp32', 'pump', 'feeder', 'relay') NOT NULL,
    status     ENUM('ON', 'OFF') DEFAULT 'OFF',
    location   VARCHAR(100),
    last_seen  TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- Bảng sensor_data
CREATE TABLE sensor_data (
    id          BIGINT      AUTO_INCREMENT PRIMARY KEY,
    device_id   VARCHAR(50) NOT NULL,
    metric_type VARCHAR(50) NOT NULL,
    value       FLOAT       NOT NULL,
    unit        VARCHAR(20),
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_sensor_device
        FOREIGN KEY (device_id) REFERENCES devices(device_id)
        ON DELETE CASCADE,

    INDEX idx_device_time (device_id, created_at),
    INDEX idx_metric_time (metric_type, created_at)
);

-- Bảng device_history
CREATE TABLE device_history (
    id         BIGINT      AUTO_INCREMENT PRIMARY KEY,
    device_id  VARCHAR(50) NOT NULL,
    action     ENUM('ON', 'OFF', 'FEED', 'RESET', 'CHANGE_WATER') NOT NULL,
    status     ENUM('success', 'failed') NOT NULL,
    source     ENUM('manual', 'api', 'schedule') NOT NULL,
    note       TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_history_device
        FOREIGN KEY (device_id) REFERENCES devices(device_id)
        ON DELETE CASCADE,

    INDEX idx_device_time (device_id, created_at)
);
```
