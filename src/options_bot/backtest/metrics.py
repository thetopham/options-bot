from __future__ import annotations


def summarize_metrics(trades: list[dict]) -> dict:
    return {"trade_count": len(trades), "profitability_claim": False}
