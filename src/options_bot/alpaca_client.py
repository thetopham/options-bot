from __future__ import annotations

from options_bot.config import Settings


def make_trading_client(settings: Settings):
    if not settings.alpaca_api_key or not settings.alpaca_secret_key:
        raise RuntimeError("Alpaca credentials are not configured")
    from alpaca.trading.client import TradingClient

    return TradingClient(settings.alpaca_api_key, settings.alpaca_secret_key, paper=settings.alpaca_paper)
