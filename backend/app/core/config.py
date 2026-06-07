from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DB_HOST: str = "localhost"
    DB_PORT: int = 3306
    DB_USER: str = "root"
    DB_PASSWORD: str = "password"
    DB_NAME: str = "iot_db"

    MQTT_HOST: str = "localhost"
    MQTT_PORT: int = 1883

    APP_ENV: str = "development"

    # ML prediction model paths (mounted via docker-compose volume)
    ML_MODEL_PATH: str = "/ml_artifacts/lstm_water_quality.pth"
    ML_SCALER_PATH: str = "/ml_artifacts/scaler.pkl"
    # Lookback window length — must match training configuration
    ML_LOOKBACK: int = 24

    @property
    def DATABASE_URL(self) -> str:
        return (
            f"mysql+aiomysql://{self.DB_USER}:{self.DB_PASSWORD}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        )

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
