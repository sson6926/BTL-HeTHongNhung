You are a senior backend engineer. Build a production-ready IoT backend system using FastAPI, MQTT, and MySQL.

## 🎯 SYSTEM OVERVIEW
This system is for aquaculture environment monitoring and control.

Devices (ESP32) send sensor data via MQTT and receive control commands via MQTT.
The backend:
- receives sensor data
- stores it in MySQL
- exposes REST APIs for dashboard
- allows users to control devices (ON/OFF)
- logs device actions

## 🧱 TECH STACK
- FastAPI (async)
- SQLAlchemy (ORM)
- MySQL
- MQTT (Eclipse Mosquitto)
- Docker + Docker Compose

---

## 🗄️ DATABASE SCHEMA

### devices
- id (PK)
- device_id (unique)
- name
- type (esp32, pump, feeder, relay)
- status (ON, OFF)
- location
- last_seen
- created_at
- updated_at

### sensor_data (LONG FORMAT)
- id (PK)
- device_id (FK)
- metric_type (temperature, ph, nh3, o2, water_level, tds, turbidity)
- value
- unit
- created_at

### device_history
- id (PK)
- device_id (FK)
- action (ON, OFF, FEED, RESET, CHANGE_WATER)
- status (success, failed)
- source (manual, api, schedule)
- note
- created_at

---

## 📡 MQTT DESIGN

### Topics:

Sensor publish:
- sensor/{device_id}/{metric_type}

Example:
- sensor/esp32_1/temperature
- sensor/esp32_1/ph

Payload:
{
  "value": 28.5,
  "unit": "C"
}

Control topics:
- control/{device_id}

Payload:
{
  "action": "ON"
}

---

## ⚙️ BACKEND FEATURES

### 1. MQTT Consumer
- Subscribe to: sensor/+/+
- Parse topic to extract device_id and metric_type
- Insert into sensor_data
- Update devices.last_seen

---

### 2. Device Control API

POST /devices/{device_id}/control

Body:
{
  "action": "ON"
}

Flow:
- Publish MQTT message to control/{device_id}
- Update devices.status
- Insert device_history (status = success)

---

### 3. Sensor APIs

GET /sensors/latest?device_id=...
→ return latest values per metric

GET /sensors/history?metric_type=temperature
→ return time series data

---

### 4. Device APIs

GET /devices
GET /devices/{id}

---

## 🧩 PROJECT STRUCTURE

backend/
│
├── app/
│   ├── main.py
│   ├── api/
│   ├── models/
│   ├── schemas/
│   ├── services/
│   ├── mqtt/
│   ├── db/
│   └── core/
│
├── Dockerfile
├── requirements.txt

---

## 🐳 DOCKER REQUIREMENTS

Create docker-compose.yml with:

### services:

1. backend (FastAPI)
- port 8000
- depends_on mysql + mqtt

2. mysql
- image: mysql:8
- database: iot_db
- user: root / password

3. mqtt (mosquitto)
- image: eclipse-mosquitto
- ports:
  - 1883:1883

---

## 📦 REQUIREMENTS.TXT

Include:
- fastapi
- uvicorn
- sqlalchemy
- pymysql
- pydantic
- python-dotenv
- paho-mqtt

---

## 🧠 IMPORTANT REQUIREMENTS

- Use async FastAPI where possible
- Use SQLAlchemy ORM (not raw SQL)
- Clean architecture (separate layers)
- Use environment variables
- Add basic logging
- Handle MQTT reconnect
- Validate input with Pydantic

---

## 🎁 OUTPUT

Generate FULL code including:

1. FastAPI app
2. SQLAlchemy models
3. MQTT consumer
4. API routes
5. Dockerfile
6. docker-compose.yml
7. requirements.txt

Make the system runnable with:

docker-compose up --build