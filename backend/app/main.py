import asyncio
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.devices import router as devices_router
from app.api.sensors import router as sensors_router
from app.db.session import init_db
from app.mqtt.client import mqtt_client

# ---------------------------------------------------------------------------
# Logging configuration
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# FastAPI application
# ---------------------------------------------------------------------------
app = FastAPI(
    title="IoT Aquaculture Backend",
    version="1.0.0",
    description="Backend system for aquaculture environment monitoring and device control.",
)

# Allow all origins in development; tighten in production via env config
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Lifecycle events
# ---------------------------------------------------------------------------


@app.on_event("startup")
async def startup() -> None:
    logger.info("Starting IoT Aquaculture Backend…")

    # Initialise database (create tables if they don't exist)
    await init_db()

    # Give the MQTT client a reference to the running event loop so that
    # paho callbacks (which run in a separate thread) can schedule coroutines.
    loop = asyncio.get_running_loop()
    mqtt_client.set_event_loop(loop)
    mqtt_client.connect()

    logger.info("Backend started successfully.")


@app.on_event("shutdown")
async def shutdown() -> None:
    logger.info("Shutting down IoT Aquaculture Backend…")
    mqtt_client.disconnect()
    logger.info("Backend shut down.")


# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------
app.include_router(devices_router, prefix="/devices", tags=["devices"])
app.include_router(sensors_router, prefix="/sensors", tags=["sensors"])


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------
@app.get("/health", tags=["health"], summary="Health check")
async def health() -> dict:
    return {"status": "ok"}
