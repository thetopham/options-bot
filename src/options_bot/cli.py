from __future__ import annotations

import typer
from rich.console import Console

from options_bot.ai.train import train_walk_forward
from options_bot.backtest.engine import BacktestEngine
from options_bot.regime.train_regimes import train_regime_model
from options_bot.execution.order_builder import build_multi_leg_order_intent
from options_bot.risk.checks import RiskLimits, evaluate_candidate
from options_bot.strategies.iron_condor import build_iron_condor
from options_bot.strategies.institutional_put_call_overlay import build_institutional_put_call_overlay
from options_bot.strategies.long_strangle import build_long_strangle
from options_bot.strategies.regime_selector import RegimeFeatures, select_regime

app = typer.Typer(help="Paper-first Alpaca options bot")
console = Console()


@app.command()
def scan(symbol: str = typer.Option(..., "--symbol")):
    decision, reason = select_regime(RegimeFeatures(iv_percentile=50, trend_strength=0.2, liquidity_score=1.0))
    console.print({"symbol": symbol, "decision": decision, "reason": reason, "safety": "paper-first/no live trading"})


@app.command()
def backtest(symbol: str = typer.Option(..., "--symbol")):
    result = BacktestEngine().run(symbol)
    console.print(result)


@app.command("paper-trade")
def paper_trade(symbol: str = typer.Option(..., "--symbol"), strategy: str = typer.Option("auto", "--strategy"), dry_run: bool = True):
    if strategy in {"auto", "condor", "iron_condor"}:
        candidate = build_iron_condor(
            symbol=symbol,
            expiration="2099-01-21",
            short_put_strike=480,
            long_put_strike=475,
            short_call_strike=520,
            long_call_strike=525,
            credit=1.25,
        )
    elif strategy in {"put_call_overlay", "institutional_put_call_overlay", "sell_put_buy_call"}:
        candidate = build_institutional_put_call_overlay(
            symbol=symbol,
            expiration="2099-01-21",
            underlying_price=500.0,
            short_put_strike=470.0,
            long_call_strike=530.0,
            put_credit=6.20,
            call_debit=1.40,
        )
    else:
        candidate = build_long_strangle(
            symbol=symbol,
            expiration="2099-01-21",
            put_strike=480,
            call_strike=520,
            debit=3.40,
        )
    decision = evaluate_candidate(candidate, RiskLimits(account_equity=100_000))
    intent = build_multi_leg_order_intent(candidate, decision, submit=not dry_run) if decision.allowed else None
    console.print({"candidate": candidate, "risk": decision, "order_intent": intent, "dry_run": dry_run})


@app.command("train-regimes")
def train_regimes(
    data_path: str = typer.Option(..., "--data-path", help="CSV or SQLite candle data path"),
    symbol: str = typer.Option("BTCUSD", "--symbol"),
    timeframe: str = typer.Option("15m", "--timeframe"),
    table: str = typer.Option("candles", "--table", help="SQLite table name when data path is a DB"),
    output_db: str | None = typer.Option(None, "--output-db", help="SQLite DB that receives regime_labels"),
):
    console.print(
        train_regime_model(
            data_path=data_path,
            symbol=symbol,
            timeframe=timeframe,
            table=table,
            output_db=output_db,
        )
    )


@app.command("train-ai")
def train_ai():
    console.print(train_walk_forward())


if __name__ == "__main__":
    app()
