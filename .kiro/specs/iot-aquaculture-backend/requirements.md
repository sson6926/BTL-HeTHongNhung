# Requirements Document

## Introduction

This document defines the requirements for a production-ready IoT backend system for aquaculture environment monitoring and control. The system enables ESP32-based sensor devices to publish environmental metrics (temperature, pH, ammonia, dissolved oxygen, water level, TDS, turbidity) over MQTT. The backend ingests this data, persists it in a MySQL database, and exposes REST APIs for a dashboard frontend. Operators can also send control commands (ON/OFF, FEED, RESET, CHANGE_WATER) to actuator devices through the same backend.

The system is containerised with Docker Compose and built on FastAPI (async), SQLAlchemy ORM, Eclipse Mosquitto, and MySQL 8.

---

## Glossary

- **System**: The IoT aquaculture backend as a whole.
- **MQTT_Consumer**: The background service that subscribes to MQTT topics and processes incoming sensor messages.
- **MQTT_Broker**: The Eclipse Mosquitto broker that routes MQTT messages between devices and the backend.
- **Device_API**: The REST API layer that handles device queries and control commands.
- **Sensor_API**: The REST API layer that handles sensor data queries.
- **Device_Service**: The service layer responsible for device state management and history logging.
- **Sensor_Service**: The service layer responsible for sensor data persistence and retrieval.
- **Device**: A registered hardware unit (ESP32, pump, feeder, or relay) identified by a unique `device_id` string.
- **SensorReading**: A single metric measurement published by a Device, stored in the `sensor_data` table.
- **DeviceHistory**: An audit record of a control action applied to a Device, stored in the `device_history` table.
- **ControlCommand**: A JSON payload sent to a Device via MQTT to change its operational state.
- **metric_type**: A string label for a sensor measurement category (e.g., `temperature`, `ph`, `nh3`, `o2`, `water_level`, `tds`, `turbidity`).
- **device_id**: A unique string identifier for a Device (e.g., `ESP32_001`, `PUMP_OXY_01`).
- **DB**: The MySQL 8 database instance named `iot_db`.
- **ORM**: SQLAlchemy async ORM used for all database interactions.
- **Pydantic_Schema**: A Pydantic v2 model used for request/response validation and serialisation.
- **Environment_Variable**: A configuration value supplied at runtime via `.env` file or Docker environment, never hard-coded.

---

## Requirements

### Requirement 1: Device Registration and Persistence

**User Story:** As a system operator, I want every device that publishes sensor data to be automatically registered in the database, so that I can track all active devices without manual setup.

#### Acceptance Criteria

1. WHEN the MQTT_Consumer receives a message on topic `sensor/{device_id}/{metric_type}` and no Device with that `device_id` exists in the DB, THEN THE MQTT_Consumer SHALL create a new Device record with `status` set to `OFF` and `type` set to `esp32`.
2. WHEN the MQTT_Consumer successfully processes a sensor message, THE MQTT_Consumer SHALL update the `last_seen` timestamp of the corresponding Device to the current UTC time.
3. THE Device_API SHALL expose a `GET /devices` endpoint that returns a list of all registered Devices.
4. THE Device_API SHALL expose a `GET /devices/{device_id}` endpoint that returns the Device record for the given `device_id`.
5. IF a `GET /devices/{device_id}` request is made for a `device_id` that does not exist in the DB, THEN THE Device_API SHALL return HTTP 404 with a descriptive error message.
6. THE System SHALL store Device records in the `devices` table with columns: `id`, `device_id`, `name`, `type`, `status`, `location`, `last_seen`, `created_at`, `updated_at`.

---

### Requirement 2: Sensor Data Ingestion via MQTT

**User Story:** As a system operator, I want the backend to automatically ingest all sensor readings published by ESP32 devices over MQTT, so that environmental data is continuously recorded without manual intervention.

#### Acceptance Criteria

1. THE MQTT_Consumer SHALL subscribe to the wildcard topic `sensor/+/+` on startup.
2. WHEN a message arrives on topic `sensor/{device_id}/{metric_type}`, THE MQTT_Consumer SHALL parse the topic to extract `device_id` and `metric_type`.
3. WHEN a valid sensor message is received, THE MQTT_Consumer SHALL validate that the payload is a JSON object containing a numeric `value` field and an optional string `unit` field.
4. WHEN a valid sensor message is received, THE MQTT_Consumer SHALL insert a SensorReading record into the `sensor_data` table with the extracted `device_id`, `metric_type`, `value`, `unit`, and current UTC timestamp.
5. IF the sensor message payload is malformed or missing the `value` field, THEN THE MQTT_Consumer SHALL log an error with the topic and raw payload and SHALL NOT insert a record into the DB.
6. THE System SHALL store SensorReading records in the `sensor_data` table with columns: `id`, `device_id`, `metric_type`, `value`, `unit`, `created_at`.
7. THE `sensor_data` table SHALL have a composite index on `(device_id, created_at)` and a composite index on `(metric_type, created_at)` to support efficient time-series queries.

---

### Requirement 3: MQTT Broker Connectivity and Reconnection

**User Story:** As a system operator, I want the backend to automatically reconnect to the MQTT broker after a connection loss, so that sensor data ingestion resumes without manual restart.

#### Acceptance Criteria

1. THE MQTT_Consumer SHALL connect to the MQTT_Broker using the host and port supplied via Environment_Variables `MQTT_HOST` and `MQTT_PORT`.
2. WHEN the connection to the MQTT_Broker is lost, THE MQTT_Consumer SHALL attempt to reconnect with an exponential back-off strategy, with a minimum retry interval of 1 second and a maximum retry interval of 60 seconds.
3. WHEN the MQTT_Consumer successfully reconnects to the MQTT_Broker, THE MQTT_Consumer SHALL re-subscribe to the `sensor/+/+` wildcard topic.
4. THE MQTT_Consumer SHALL log each connection attempt, successful connection, disconnection, and reconnection event at INFO level.
5. WHILE the MQTT_Consumer is disconnected from the MQTT_Broker, THE System SHALL continue to serve REST API requests without returning errors caused by the MQTT disconnection.

---

### Requirement 4: Device Control via REST API and MQTT

**User Story:** As a dashboard operator, I want to send control commands to devices through a REST API, so that I can remotely manage actuators such as pumps and feeders.

#### Acceptance Criteria

1. THE Device_API SHALL expose a `POST /devices/{device_id}/control` endpoint that accepts a JSON body containing an `action` field.
2. THE `action` field SHALL accept one of the following values: `ON`, `OFF`, `FEED`, `RESET`, `CHANGE_WATER`.
3. IF the `action` field contains a value not in the allowed set, THEN THE Device_API SHALL return HTTP 422 with a descriptive validation error.
4. WHEN a valid control request is received, THE Device_Service SHALL publish a ControlCommand JSON payload `{"action": "<action>"}` to the MQTT topic `control/{device_id}`.
5. WHEN a valid control request is received and the MQTT publish succeeds, THE Device_Service SHALL update the Device `status` field to the new action value for `ON` and `OFF` actions.
6. WHEN a valid control request is received, THE Device_Service SHALL insert a DeviceHistory record with `action`, `status` set to `success`, `source` set to `api`, and an optional `note`.
7. IF the MQTT publish fails, THEN THE Device_Service SHALL insert a DeviceHistory record with `status` set to `failed` and SHALL return HTTP 502 with a descriptive error message.
8. IF a control request is made for a `device_id` that does not exist in the DB, THEN THE Device_API SHALL return HTTP 404 with a descriptive error message.
9. THE System SHALL store DeviceHistory records in the `device_history` table with columns: `id`, `device_id`, `action`, `status`, `source`, `note`, `created_at`.

---

### Requirement 5: Sensor Data Query APIs

**User Story:** As a dashboard developer, I want REST endpoints to retrieve the latest sensor readings and historical time-series data, so that I can display real-time and trend information to operators.

#### Acceptance Criteria

1. THE Sensor_API SHALL expose a `GET /sensors/latest` endpoint that accepts an optional `device_id` query parameter.
2. WHEN `GET /sensors/latest` is called with a `device_id` parameter, THE Sensor_API SHALL return the most recent SensorReading for each distinct `metric_type` associated with that Device.
3. WHEN `GET /sensors/latest` is called without a `device_id` parameter, THE Sensor_API SHALL return the most recent SensorReading for each distinct `(device_id, metric_type)` combination across all Devices.
4. THE Sensor_API SHALL expose a `GET /sensors/history` endpoint that accepts a required `metric_type` query parameter and optional `device_id`, `start_time`, and `end_time` query parameters.
5. WHEN `GET /sensors/history` is called, THE Sensor_API SHALL return all SensorReading records matching the provided filters, ordered by `created_at` ascending.
6. IF the `metric_type` query parameter is missing from a `GET /sensors/history` request, THEN THE Sensor_API SHALL return HTTP 422 with a descriptive validation error.
7. THE Sensor_API SHALL return sensor data responses serialised as JSON using Pydantic_Schema models, including `id`, `device_id`, `metric_type`, `value`, `unit`, and `created_at` fields.

---

### Requirement 6: Input Validation and Error Handling

**User Story:** As a developer integrating with the API, I want all inputs to be validated and errors to return structured responses, so that I can reliably detect and handle failures in my client code.

#### Acceptance Criteria

1. THE System SHALL validate all incoming REST API request bodies and query parameters using Pydantic_Schema models before processing.
2. IF a request body fails Pydantic_Schema validation, THEN THE System SHALL return HTTP 422 with a JSON body describing each validation error field and message.
3. IF an unhandled exception occurs during request processing, THEN THE System SHALL return HTTP 500 with a generic error message and SHALL log the full exception traceback at ERROR level.
4. THE System SHALL log all incoming API requests at INFO level, including HTTP method, path, and response status code.
5. THE System SHALL use structured logging with a consistent format including timestamp, log level, logger name, and message.

---

### Requirement 7: Database Configuration and ORM

**User Story:** As a developer, I want all database interactions to use SQLAlchemy ORM with async support, so that the system is maintainable, type-safe, and non-blocking under concurrent load.

#### Acceptance Criteria

1. THE System SHALL use SQLAlchemy async ORM for all DB read and write operations, with no raw SQL strings in application code.
2. THE System SHALL read the DB connection URL from the Environment_Variable `DATABASE_URL`.
3. THE System SHALL use a connection pool with configurable pool size supplied via Environment_Variables.
4. WHEN the application starts, THE System SHALL verify the DB connection is reachable and log the result at INFO level.
5. THE System SHALL define all ORM models in a dedicated `models/` module, with each table represented by a separate Python class.

---

### Requirement 8: Configuration via Environment Variables

**User Story:** As a DevOps engineer, I want all runtime configuration to be supplied through environment variables, so that the same Docker image can be deployed to different environments without code changes.

#### Acceptance Criteria

1. THE System SHALL read the following Environment_Variables at startup: `DATABASE_URL`, `MQTT_HOST`, `MQTT_PORT`, `MQTT_CLIENT_ID`, `LOG_LEVEL`.
2. IF a required Environment_Variable is missing at startup, THEN THE System SHALL log a descriptive error and exit with a non-zero status code.
3. THE System SHALL support loading Environment_Variables from a `.env` file using `python-dotenv` when the file is present.
4. THE System SHALL never hard-code credentials, hostnames, or port numbers in application source code.

---

### Requirement 9: Containerisation with Docker Compose

**User Story:** As a developer, I want the entire system to start with a single `docker-compose up --build` command, so that local development and deployment are reproducible and consistent.

#### Acceptance Criteria

1. THE System SHALL provide a `docker-compose.yml` that defines three services: `backend`, `mysql`, and `mqtt`.
2. THE `backend` service SHALL build from a `Dockerfile` in the `backend/` directory and expose port `8000`.
3. THE `mysql` service SHALL use the `mysql:8` image, initialise the `iot_db` database, and persist data using a named Docker volume.
4. THE `mqtt` service SHALL use the `eclipse-mosquitto` image and expose port `1883`.
5. THE `backend` service SHALL declare `depends_on` for both `mysql` and `mqtt` services.
6. THE System SHALL provide a `backend/requirements.txt` listing all Python dependencies with pinned versions, including `fastapi`, `uvicorn`, `sqlalchemy`, `aiomysql`, `pydantic`, `python-dotenv`, and `paho-mqtt`.
7. THE `backend` Dockerfile SHALL use a slim Python base image and install dependencies from `requirements.txt`.

---

### Requirement 10: Project Structure and Clean Architecture

**User Story:** As a developer, I want the codebase to follow a clean layered architecture, so that each concern is isolated and the system is easy to extend and test.

#### Acceptance Criteria

1. THE System SHALL organise application code under `backend/app/` with the following sub-packages: `api/`, `models/`, `schemas/`, `services/`, `mqtt/`, `db/`, `core/`.
2. THE `api/` package SHALL contain only route handlers that delegate business logic to the `services/` layer.
3. THE `services/` package SHALL contain business logic and SHALL interact with the DB only through ORM models, not through direct SQL.
4. THE `models/` package SHALL contain SQLAlchemy ORM model definitions only.
5. THE `schemas/` package SHALL contain Pydantic_Schema definitions for request and response serialisation only.
6. THE `mqtt/` package SHALL contain the MQTT_Consumer implementation and SHALL delegate DB writes to the `services/` layer.
7. THE `core/` package SHALL contain application configuration loading and logging setup.
8. THE `db/` package SHALL contain the async SQLAlchemy engine, session factory, and dependency injection helpers.
