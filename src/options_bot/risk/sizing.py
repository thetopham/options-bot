from __future__ import annotations


def max_contracts_for_risk(account_equity: float, max_risk_fraction: float, max_loss_per_contract: float) -> int:
    if max_loss_per_contract <= 0:
        return 0
    return int((account_equity * max_risk_fraction) // max_loss_per_contract)
