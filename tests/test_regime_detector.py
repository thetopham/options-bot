from __future__ import annotations

import sqlite3

import numpy as np
import pandas as pd

from options_bot.regime.regime_detector import (
    HMMCandidateResult,
    compute_regime_features,
    select_best_model,
    time_train_test_split,
)
from options_bot.regime.analyze_regimes import compute_regime_statistics
from options_bot.regime.migrations import ensure_regime_labels_table, write_regime_labels


def _sample_candles(rows: int = 80) -> pd.DataFrame:
    idx = pd.date_range("2026-01-01", periods=rows, freq="15min", tz="UTC")
    close = 100 + np.cumsum(np.sin(np.arange(rows) / 5) * 0.3 + 0.05)
    volume = 1000 + np.cos(np.arange(rows) / 3) * 100
    return pd.DataFrame(
        {
            "timestamp": idx,
            "open": close - 0.1,
            "high": close + 0.3,
            "low": close - 0.4,
            "close": close,
            "volume": volume,
            "spread": np.linspace(0.01, 0.03, rows),
            "orderbook_imbalance": np.linspace(-0.25, 0.25, rows),
        }
    )


def test_compute_regime_features_are_lagged_and_have_expected_columns():
    candles = _sample_candles()

    features = compute_regime_features(candles, price_col="close")

    expected = {
        "return_1",
        "return_3",
        "return_12",
        "rolling_vol_12",
        "rolling_vol_48",
        "rolling_realized_var_12",
        "rolling_slope_12",
        "rolling_slope_48",
        "distance_from_ma_48",
        "volume_zscore_48",
        "spread",
        "orderbook_imbalance",
    }
    assert expected.issubset(set(features.columns))
    first_feature_ts = features["timestamp"].min()
    first_idx = candles.index[candles["timestamp"] == first_feature_ts][0]
    previous_close = candles.loc[first_idx - 1, "close"]
    current_close = candles.loc[first_idx, "close"]
    assert features.loc[features["timestamp"] == first_feature_ts, "return_1"].iloc[0] != np.log(current_close / previous_close)


def test_time_train_test_split_preserves_chronological_order():
    features = compute_regime_features(_sample_candles())

    train, test = time_train_test_split(features, test_fraction=0.25)

    assert len(train) > 0
    assert len(test) > 0
    assert train["timestamp"].max() < test["timestamp"].min()


def test_select_best_model_prefers_lower_bic_then_oos_log_likelihood():
    candidates = [
        HMMCandidateResult(n_states=2, aic=110.0, bic=95.0, train_log_likelihood=-50.0, test_log_likelihood=-30.0),
        HMMCandidateResult(n_states=3, aic=100.0, bic=90.0, train_log_likelihood=-45.0, test_log_likelihood=-31.0),
        HMMCandidateResult(n_states=4, aic=105.0, bic=90.0, train_log_likelihood=-44.0, test_log_likelihood=-20.0),
    ]

    best = select_best_model(candidates)

    assert best.n_states == 4


def test_regime_labels_migration_and_write_roundtrip(tmp_path):
    db_path = tmp_path / "regimes.sqlite3"
    labels = pd.DataFrame(
        {
            "timestamp": ["2026-01-01T00:00:00Z", "2026-01-01T00:15:00Z"],
            "symbol": ["BTCUSD", "BTCUSD"],
            "timeframe": ["15m", "15m"],
            "model_version": ["hmm-v1", "hmm-v1"],
            "regime_id": [0, 1],
            "regime_name": ["chop_range", "low_vol_trend"],
            "regime_probability": [0.7, 0.8],
        }
    )

    with sqlite3.connect(db_path) as conn:
        ensure_regime_labels_table(conn)
        written = write_regime_labels(conn, labels)
        rows = conn.execute("select symbol, timeframe, regime_id, regime_name from regime_labels order by timestamp").fetchall()

    assert written == 2
    assert rows == [("BTCUSD", "15m", 0, "chop_range"), ("BTCUSD", "15m", 1, "low_vol_trend")]


def test_compute_regime_statistics_reports_persistence_and_feature_means():
    labels = pd.DataFrame({"regime_id": [0, 0, 1, 1, 1, 0], "regime_name": ["chop", "chop", "trend", "trend", "trend", "chop"]})
    features = pd.DataFrame({"return_1": [0.0, 0.1, 0.3, 0.2, 0.4, -0.1], "rolling_vol_12": [1, 1, 2, 2, 3, 1]})

    stats = compute_regime_statistics(labels, features)

    assert stats[0]["count"] == 3
    assert stats[1]["count"] == 3
    assert stats[1]["persistence"] > stats[0]["persistence"]
    assert "return_1" in stats[1]["feature_means"]
