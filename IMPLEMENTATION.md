# Implementation Plan

## Architecture

The bot is split into explicit layers:

1. **Config:** pydantic settings from `.env`, with paper mode default and no hardcoded secrets.
2. **Alpaca client:** lazy factory for Alpaca TradingClient and data clients.
3. **Data:** option contracts, option chains, bars, and snapshots.
4. **Strategies:** pure builders for iron condor, long strangle, cash-secured put/call overlay, and regime selection.
5. **Regime research:** Markov/HMM feature engineering, model selection, labels, transition matrices, and SQLite persistence.
6. **Risk:** liquidity checks, sizing, max loss, max daily loss, max positions, kill switch.
7. **Backtest:** chronological engine and metrics stubs.
8. **Execution:** order-intent builder, paper order adapter, position manager.
9. **AI:** feature engineering, baseline model, walk-forward training, explainability.
10. **CLI:** Rich/Typer commands for scan, backtest, paper-trade, train-regimes, and train-ai.

## Build Order

### Phase 0: Safety-first scaffold

- Add `.env.example`, `pyproject.toml`, `README.md`, `PRD.md`, `IMPLEMENTATION.md`.
- Add package skeleton under `src/options_bot`.
- Add tests for strategy construction and risk rejection.

### Phase 1: Deterministic strategy objects

- Define `OptionLeg`, `StrategyCandidate`, `RiskLimits`, and `RiskDecision` models.
- Implement iron condor and long strangle constructors.
- Implement breakeven and max profit/loss calculations.

### Phase 2: Guardrails

- Reject market orders.
- Reject naked short options.
- Reject missing protective wings.
- Reject bid/ask spreads above threshold.
- Reject low open interest / volume.
- Enforce max risk per trade and kill switch.

### Phase 3: Alpaca integration

- Add client factories for `alpaca-py`.
- Keep order submission behind paper mode and explicit `submit=False` default.
- Build multi-leg order intents before actual paper submission.

### Phase 4: Research and backtest

- Add data normalizers for chains, bars, and snapshots.
- Implement chronological backtest engine.
- Add walk-forward train/evaluate split.
- Store runs in SQLite or DuckDB.

### Phase 5: Markov/HMM regime detector

- Compute lagged BTC 15m features: returns, volatility, realized variance, slope, distance from moving average, volume z-score, spread, and orderbook imbalance.
- Train HMM candidates with 2-6 states using chronological splits only.
- Select by BIC and out-of-sample log likelihood.
- Persist labels to SQLite table `regime_labels`.
- Use transition matrices, persistence, and feature means as diagnostics before wiring strategy filters.

### Phase 6: AI regime selector

- Start with transparent baseline rules.
- Add sklearn model only after baseline metrics exist.
- Persist feature set and labels with timestamps.
- Explain every no-trade / condor / strangle decision.

## Safety Boundary

Default mode is `paper`. Live mode is not enabled by this scaffold. Future live mode must require:

- Explicit user approval in the current session.
- Config flag beyond `.env` defaults.
- Tests proving live gates fail closed.
- Code review of broker endpoints and risk caps.

## Verification

- `python -m pytest -q`
- `python -m options_bot.cli scan --symbol SPY`
- `python -m options_bot.cli backtest --symbol SPY`
- `python -m options_bot.cli paper-trade --symbol SPY --strategy auto --dry-run`
- `python -m options_bot.cli train-regimes --data-path data/btc_15m.csv --symbol BTCUSD --timeframe 15m --output-db data/regimes.sqlite3`
- `python -m options_bot.cli train-ai`
