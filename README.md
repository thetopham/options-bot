# Options Bot

Paper-first Alpaca options research and paper-trading scaffold for iron condors, long strangles, and an explainable regime selector.

## Safety boundary

- Defaults to paper mode.
- Does not enable live trading.
- Does not hardcode secrets.
- Does not submit orders unless explicitly wired for Alpaca paper trading.
- No market orders for options.
- No naked short options.

## Setup

```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
cp .env.example .env
```

Set Alpaca credentials in `.env`.

## Commands

```bash
options-bot scan --symbol SPY
options-bot backtest --symbol SPY
options-bot paper-trade --symbol SPY --strategy auto --dry-run
options-bot paper-trade --symbol SPY --strategy put_call_overlay --dry-run
options-bot train-regimes --data-path data/btc_15m.csv --symbol BTCUSD --timeframe 15m --output-db data/regimes.sqlite3
options-bot train-ai
```

## Framing

- Condor = sell expensive fear when range is likely.
- Strangle = buy cheap vol when a big move is likely.
- Put/call overlay = sell cash-secured downside liquidity, use premium for OTM upside convexity.
- Markov/HMM regimes = regime brain for chop/trend/high-vol filters.
- AI = regime filter, not a magic predictor.

No profitability is claimed.
