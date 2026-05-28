from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

RegimeDecision = Literal["no_trade", "iron_condor", "long_strangle"]


@dataclass
class RegimeFeatures:
    iv_percentile: float
    trend_strength: float
    event_risk: float = 0.0
    liquidity_score: float = 1.0


def select_regime(features: RegimeFeatures) -> tuple[RegimeDecision, str]:
    if features.liquidity_score < 0.5:
        return "no_trade", "No trade: liquidity score below threshold."
    if features.iv_percentile >= 70 and features.trend_strength <= 0.35 and features.event_risk < 0.5:
        return "iron_condor", "High IV with weak trend and low event risk favors range-premium condor research."
    if features.iv_percentile <= 30 and (features.trend_strength >= 0.6 or features.event_risk >= 0.6):
        return "long_strangle", "Low IV with trend/event catalyst favors long-vol strangle research."
    return "no_trade", "No trade: regime evidence is mixed or insufficient."
