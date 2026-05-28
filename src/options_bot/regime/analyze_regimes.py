from __future__ import annotations

import pandas as pd


def compute_regime_statistics(labels: pd.DataFrame, features: pd.DataFrame | None = None) -> dict[int, dict]:
    if "regime_id" not in labels.columns:
        raise ValueError("labels must include regime_id")
    stats: dict[int, dict] = {}
    regime_ids = labels["regime_id"].astype(int).tolist()
    for regime_id in sorted(set(regime_ids)):
        mask = labels["regime_id"].astype(int) == regime_id
        count = int(mask.sum())
        stay = 0
        total_transitions = 0
        for a, b in zip(regime_ids[:-1], regime_ids[1:]):
            if a == regime_id:
                total_transitions += 1
                if b == regime_id:
                    stay += 1
        feature_means = {}
        if features is not None:
            numeric = features.loc[mask.values].select_dtypes(include="number")
            feature_means = {k: float(v) for k, v in numeric.mean().dropna().to_dict().items()}
        name = labels.loc[mask, "regime_name"].iloc[0] if "regime_name" in labels.columns and count else str(regime_id)
        stats[int(regime_id)] = {
            "name": name,
            "count": count,
            "persistence": float(stay / total_transitions) if total_transitions else 0.0,
            "feature_means": feature_means,
        }
    return stats


def summarize_transition_matrix(labels: pd.DataFrame) -> pd.DataFrame:
    from options_bot.regime.regime_detector import transition_matrix

    return transition_matrix(labels["regime_id"].to_numpy())
