# BTC 15m Markov/HMM Regime Detector

Research-only market-regime module for BTC 15m candles/orderbook features.

## Purpose

Markov/HMM models are the **regime brain**:

- infer hidden states from returns, volatility, slope, distance from mean, volume, spread, and imbalance;
- estimate state-transition probabilities;
- label each timestamp with the most likely hidden regime;
- feed risk/strategy filters such as block chop, reduce size in high-volatility, allow low-volatility trend setups.

This module does **not** claim profitability and does not place orders.

## Features

`compute_regime_features()` creates lagged features so prediction at timestamp `t` only uses data available through `t-1`:

- `return_1`
- `return_3`
- `return_12`
- `rolling_vol_12`
- `rolling_vol_48`
- `rolling_realized_var_12`
- `rolling_slope_12`
- `rolling_slope_48`
- `distance_from_ma_48`
- `volume_zscore_48`
- `spread`
- `orderbook_imbalance`

## Model selection

`fit_hmm_candidates()` trains Gaussian HMMs with 2-6 states, then selects by:

1. lower BIC;
2. higher out-of-sample log likelihood;
3. lower state count as tie-breaker.

Splits are chronological. There are no random shuffled splits.

## SQLite output

Migration creates:

```sql
create table if not exists regime_labels (
    timestamp text not null,
    symbol text not null,
    timeframe text not null,
    model_version text not null,
    regime_id integer not null,
    regime_name text not null,
    regime_probability real not null,
    created_at text not null default current_timestamp,
    primary key (timestamp, symbol, timeframe, model_version)
);
```

## CLI

```bash
options-bot train-regimes \
  --data-path data/btc_15m.csv \
  --symbol BTCUSD \
  --timeframe 15m \
  --output-db data/regimes.sqlite3
```

For SQLite candle input:

```bash
options-bot train-regimes \
  --data-path data/market.sqlite3 \
  --table candles \
  --symbol BTCUSD \
  --timeframe 15m \
  --output-db data/regimes.sqlite3
```

Expected input columns:

- required: `timestamp`, `close`
- recommended: `open`, `high`, `low`, `volume`, `spread`, `orderbook_imbalance`

## Next research step

Compare strategy metrics with and without regime labels:

- block trades in `chop_range`;
- reduce size in `high_volatility` / `high_vol_down_or_panic`;
- allow trend setups in `low_vol_trend_up` or `trend_down` only when strategy direction agrees.
