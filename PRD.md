# PRD: Paper-First Alpaca Options Bot

## Product Summary

Create a Python 3.11+ options research and paper-trading bot using Alpaca's official `alpaca-py` SDK. The system supports three strategy decisions:

- **Iron condor:** sell expensive fear when a range-bound outcome is likely.
- **Long strangle:** buy cheap volatility when a large move is likely.
- **AI regime selector:** choose no-trade / condor / strangle as a regime filter, not a magic predictor.

The product is **paper-trading first**. Live trading is not implemented as a default path and must require explicit human approval, config gates, and code review before any future activation.

## Goals

1. Research Alpaca option chains, market data, snapshots, and liquidity.
2. Build explainable iron condor and long strangle candidates.
3. Backtest strategy rules with chronological / walk-forward validation.
4. Simulate and eventually submit paper multi-leg option orders through Alpaca paper workflows.
5. Enforce risk guardrails before any order payload is built or submitted.
6. Log every decision with rationale, max profit/loss, breakevens, liquidity warnings, and exit plan.

## Non-Goals

- No profitability claims.
- No live trading in v1.
- No naked short options.
- No market orders for options.
- No one-symbol / one-period optimized “edge” claims.
- No secret hardcoding.

## Users

- Quant developer researching options strategies.
- Risk manager reviewing trade eligibility and paper-trade logs.
- Future operator who may run scan, backtest, train, and paper-trade commands.

## Functional Requirements

### CLI

- `options-bot scan --symbol SPY`
- `options-bot backtest --symbol SPY`
- `options-bot paper-trade --symbol SPY --strategy auto`
- `options-bot train-ai`

### Strategies

#### Iron Condor

Use when IV percentile is high and realized trend/range model predicts containment.

Candidate construction:

- Expiration target: 7-45 DTE.
- Sell OTM call spread and OTM put spread.
- Short strikes around 10-25 delta.
- Buy protective wings farther OTM.
- Require minimum credit, bounded max loss, bid/ask sanity, open interest, and volume.

Exit plan:

- Take profit at 40-60% max profit.
- Stop at 1.5-2x credit loss.
- Close before expiration.

#### Long Strangle

Use when IV percentile is low and an event/momentum/vol-expansion model predicts a large move.

Candidate construction:

- Buy OTM call and OTM put.
- Pick expiration with enough time for the move.
- Require low spread, sufficient liquidity, and bounded max debit.

Exit plan:

- Profit target.
- IV crush warning.
- Time decay threshold.
- Trend failure.

### AI Regime Selector

Inputs:

- Underlying returns.
- Realized volatility.
- Implied volatility percentile/rank.
- IV vs RV spread.
- Option chain skew.
- VIX/SPY regime if available.
- Earnings/events calendar placeholder.
- Trend strength.
- Realized range vs expected move.
- Liquidity scores.
- Bid/ask spread scores.

Labels:

- Condor edge worked.
- Strangle edge worked.
- No-trade was best.

Validation:

- Walk-forward only.
- No random train/test leakage.
- Baseline rules before complex ML.

## Safety Requirements

- Paper trading only by default.
- Max risk per trade: 0.5%-1% account equity.
- Max daily loss.
- Max open positions.
- No options market orders.
- No naked short options.
- All short legs require protective long legs.
- Reject illiquid chains.
- Human approval required for future live mode.
- Kill switch blocks order creation/submission.

## Success Criteria for v1 Scaffold

- Repository structure exists.
- Docs explain setup, safety boundary, and commands.
- Strategy builders create structured candidate objects.
- Risk checks reject unsafe or illiquid candidates.
- Paper order builder creates multi-leg order intents but does not submit by default.
- Tests cover strategy construction and risk rejection.
- Backtest engine stub runs without claiming performance.
