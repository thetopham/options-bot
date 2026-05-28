from __future__ import annotations

import sqlite3
from pathlib import Path

from options_bot.regime.migrations import ensure_regime_labels_table, write_regime_labels
from options_bot.regime.regime_detector import compute_regime_features, fit_hmm_candidates, label_regimes, load_market_data


def train_regime_model(
    *,
    data_path: str | Path,
    symbol: str = "BTCUSD",
    timeframe: str = "15m",
    table: str = "candles",
    output_db: str | Path | None = None,
    model_version: str = "hmm-v1",
) -> dict:
    raw = load_market_data(data_path, table=table)
    features = compute_regime_features(raw)
    best, candidates = fit_hmm_candidates(features)
    labels = label_regimes(best.model, features, symbol=symbol, timeframe=timeframe, model_version=model_version)
    written = 0
    if output_db is not None:
        with sqlite3.connect(output_db) as conn:
            ensure_regime_labels_table(conn)
            written = write_regime_labels(conn, labels)
    return {
        "symbol": symbol,
        "timeframe": timeframe,
        "model_version": model_version,
        "feature_rows": len(features),
        "best_n_states": best.n_states,
        "best_aic": best.aic,
        "best_bic": best.bic,
        "best_test_log_likelihood": best.test_log_likelihood,
        "candidate_count": len(candidates),
        "labels_written": written,
    }
