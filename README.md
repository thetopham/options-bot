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
options-bot train-ai
```

## Framing

- Condor = sell expensive fear when range is likely.
- Strangle = buy cheap vol when a big move is likely.
- AI = regime filter, not a magic predictor.

No profitability is claimed.
