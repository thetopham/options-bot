from __future__ import annotations

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    alpaca_api_key: str = Field(default="", alias="ALPACA_API_KEY")
    alpaca_secret_key: str = Field(default="", alias="ALPACA_SECRET_KEY")
    alpaca_paper: bool = Field(default=True, alias="ALPACA_PAPER")
    database_url: str = Field(default="duckdb:///options_bot.duckdb", alias="DATABASE_URL")
    max_risk_fraction: float = Field(default=0.01, alias="MAX_RISK_FRACTION")
    max_daily_loss: float = Field(default=1000.0, alias="MAX_DAILY_LOSS")
    max_open_positions: int = Field(default=5, alias="MAX_OPEN_POSITIONS")

    @property
    def live_enabled(self) -> bool:
        return False


def get_settings() -> Settings:
    return Settings()
