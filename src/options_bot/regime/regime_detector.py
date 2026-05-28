from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

FEATURE_COLUMNS = [
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
]


@dataclass(frozen=True)
class HMMCandidateResult:
    n_states: int
    aic: float
    bic: float
    train_log_likelihood: float
    test_log_likelihood: float
    model: object | None = None


def load_market_data(path: str | Path, *, table: str = "candles") -> pd.DataFrame:
    path = Path(path)
    if path.suffix.lower() == ".csv":
        df = pd.read_csv(path)
    else:
        import sqlite3
        with sqlite3.connect(path) as conn:
            df = pd.read_sql_query(f"select * from {table} order by timestamp", conn)
    if "timestamp" not in df.columns:
        raise ValueError("market data must include timestamp")
    df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)
    return df.sort_values("timestamp").reset_index(drop=True)


def compute_regime_features(df: pd.DataFrame, *, price_col: str = "close") -> pd.DataFrame:
    if price_col not in df.columns:
        raise ValueError(f"missing price column: {price_col}")
    work = df.sort_values("timestamp").reset_index(drop=True).copy()
    price = work[price_col].astype(float)
    log_price = np.log(price)
    log_return = log_price.diff()

    # Build features from information available through t-1, then assign them to t.
    past_return = log_return.shift(1)
    out = pd.DataFrame({"timestamp": pd.to_datetime(work["timestamp"], utc=True)})
    out["return_1"] = past_return
    out["return_3"] = past_return.rolling(3).sum()
    out["return_12"] = past_return.rolling(12).sum()
    out["rolling_vol_12"] = past_return.rolling(12).std()
    out["rolling_vol_48"] = past_return.rolling(48).std()
    out["rolling_realized_var_12"] = past_return.pow(2).rolling(12).sum()
    out["rolling_slope_12"] = _rolling_slope(log_price.shift(1), 12)
    out["rolling_slope_48"] = _rolling_slope(log_price.shift(1), 48)
    ma_48 = price.shift(1).rolling(48).mean()
    out["distance_from_ma_48"] = (price.shift(1) - ma_48) / ma_48
    if "volume" in work.columns:
        volume = work["volume"].astype(float).shift(1)
        out["volume_zscore_48"] = (volume - volume.rolling(48).mean()) / volume.rolling(48).std()
    else:
        out["volume_zscore_48"] = 0.0
    out["spread"] = work["spread"].astype(float).shift(1) if "spread" in work.columns else 0.0
    out["orderbook_imbalance"] = work["orderbook_imbalance"].astype(float).shift(1) if "orderbook_imbalance" in work.columns else 0.0
    return out.dropna().reset_index(drop=True)


def _rolling_slope(series: pd.Series, window: int) -> pd.Series:
    x = np.arange(window, dtype=float)
    x = x - x.mean()
    denom = float((x * x).sum())

    def slope(values: np.ndarray) -> float:
        y = values.astype(float)
        return float(((y - y.mean()) * x).sum() / denom)

    return series.rolling(window).apply(slope, raw=True)


def time_train_test_split(features: pd.DataFrame, *, test_fraction: float = 0.25) -> tuple[pd.DataFrame, pd.DataFrame]:
    if not 0 < test_fraction < 1:
        raise ValueError("test_fraction must be between 0 and 1")
    ordered = features.sort_values("timestamp").reset_index(drop=True)
    split = int(len(ordered) * (1 - test_fraction))
    if split <= 0 or split >= len(ordered):
        raise ValueError("not enough rows for chronological train/test split")
    return ordered.iloc[:split].copy(), ordered.iloc[split:].copy()


def select_best_model(candidates: list[HMMCandidateResult]) -> HMMCandidateResult:
    if not candidates:
        raise ValueError("no candidate models")
    return sorted(candidates, key=lambda c: (c.bic, -c.test_log_likelihood, c.n_states))[0]


def fit_hmm_candidates(
    features: pd.DataFrame,
    *,
    state_counts: range = range(2, 7),
    test_fraction: float = 0.25,
    random_state: int = 7,
) -> tuple[HMMCandidateResult, list[HMMCandidateResult]]:
    train, test = time_train_test_split(features, test_fraction=test_fraction)
    x_train = train[FEATURE_COLUMNS].to_numpy(dtype=float)
    x_test = test[FEATURE_COLUMNS].to_numpy(dtype=float)
    try:
        from hmmlearn.hmm import GaussianHMM
    except ImportError as exc:
        raise RuntimeError("Install hmmlearn to train HMM regimes: pip install hmmlearn") from exc
    candidates: list[HMMCandidateResult] = []
    for n_states in state_counts:
        model = GaussianHMM(n_components=n_states, covariance_type="diag", n_iter=250, random_state=random_state)
        model.fit(x_train)
        train_ll = float(model.score(x_train))
        test_ll = float(model.score(x_test))
        n_features = x_train.shape[1]
        # Approximate parameter count: transitions + start probs + Gaussian means/diag variances.
        params = (n_states * (n_states - 1)) + (n_states - 1) + (2 * n_states * n_features)
        aic = 2 * params - 2 * train_ll
        bic = np.log(len(x_train)) * params - 2 * train_ll
        candidates.append(HMMCandidateResult(n_states, float(aic), float(bic), train_ll, test_ll, model))
    return select_best_model(candidates), candidates


def label_regimes(model: object, features: pd.DataFrame, *, symbol: str, timeframe: str, model_version: str) -> pd.DataFrame:
    x = features[FEATURE_COLUMNS].to_numpy(dtype=float)
    states = model.predict(x)
    probabilities = model.predict_proba(x).max(axis=1) if hasattr(model, "predict_proba") else np.ones(len(states))
    names = map_regime_names(features, states)
    return pd.DataFrame(
        {
            "timestamp": features["timestamp"].astype(str),
            "symbol": symbol,
            "timeframe": timeframe,
            "model_version": model_version,
            "regime_id": states.astype(int),
            "regime_name": [names[int(state)] for state in states],
            "regime_probability": probabilities.astype(float),
        }
    )


def map_regime_names(features: pd.DataFrame, states: np.ndarray) -> dict[int, str]:
    mapping: dict[int, str] = {}
    state_series = pd.Series(states, index=features.index)
    global_vol = features["rolling_vol_12"].median()
    for state in sorted(set(map(int, states))):
        rows = features[state_series == state]
        ret = rows["return_12"].mean()
        vol = rows["rolling_vol_12"].mean()
        slope = rows["rolling_slope_12"].mean()
        if vol > global_vol * 1.25 and ret < 0:
            name = "high_vol_down_or_panic"
        elif vol > global_vol * 1.25:
            name = "high_volatility"
        elif ret > 0 and slope > 0:
            name = "low_vol_trend_up"
        elif ret < 0 and slope < 0:
            name = "trend_down"
        else:
            name = "chop_range"
        mapping[state] = name
    return mapping


def transition_matrix(states: np.ndarray) -> pd.DataFrame:
    unique = sorted(set(map(int, states)))
    idx = {state: i for i, state in enumerate(unique)}
    counts = np.zeros((len(unique), len(unique)), dtype=float)
    for a, b in zip(states[:-1], states[1:]):
        counts[idx[int(a)], idx[int(b)]] += 1
    probs = counts / np.where(counts.sum(axis=1, keepdims=True) == 0, 1, counts.sum(axis=1, keepdims=True))
    return pd.DataFrame(probs, index=unique, columns=unique)
