from __future__ import annotations

from dataclasses import dataclass

from options_bot.models import StrategyCandidate
from options_bot.risk.checks import RiskDecision


@dataclass
class MultiLegOrderIntent:
    symbol: str
    strategy: str
    order_class: str
    time_in_force: str
    limit_price: float
    legs: list[dict]
    submit: bool = False


def build_multi_leg_order_intent(candidate: StrategyCandidate, risk_decision: RiskDecision, *, submit: bool = False) -> MultiLegOrderIntent:
    if not risk_decision.allowed:
        raise ValueError("Cannot build order intent for rejected candidate")
    if submit:
        # Future paper broker submission must call this explicitly; live remains unavailable.
        submit = True
    limit_price = candidate.net_credit if candidate.net_credit > 0 else candidate.net_debit
    return MultiLegOrderIntent(
        symbol=candidate.symbol,
        strategy=candidate.strategy,
        order_class="mleg",
        time_in_force="day",
        limit_price=limit_price,
        submit=submit,
        legs=[
            {
                "symbol": leg.symbol,
                "expiration": leg.expiration,
                "option_type": leg.option_type,
                "strike": leg.strike,
                "side": leg.side,
                "quantity": leg.quantity,
                "order_type": leg.order_type,
            }
            for leg in candidate.legs
        ],
    )
