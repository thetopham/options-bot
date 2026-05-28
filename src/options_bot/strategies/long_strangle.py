from __future__ import annotations

from options_bot.models import OptionLeg, StrategyCandidate

CONTRACT_MULTIPLIER = 100


def build_long_strangle(
    *,
    symbol: str,
    expiration: str,
    put_strike: float,
    call_strike: float,
    debit: float,
) -> StrategyCandidate:
    if not put_strike < call_strike:
        raise ValueError("Long strangle requires put strike below call strike")
    legs = [
        OptionLeg(symbol, expiration, "put", put_strike, "buy"),
        OptionLeg(symbol, expiration, "call", call_strike, "buy"),
    ]
    return StrategyCandidate(
        symbol=symbol,
        strategy="long_strangle",
        expiration=expiration,
        legs=legs,
        net_debit=debit,
        max_profit=None,
        max_loss=round(debit * CONTRACT_MULTIPLIER, 2),
        breakevens=[round(put_strike - debit, 2), round(call_strike + debit, 2)],
        explanation=(
            "Long strangle candidate: buy relatively cheap vol when event, momentum, or volatility "
            "expansion conditions suggest a large move may occur."
        ),
        exit_plan="Exit on profit target, IV crush warning, time decay threshold, or trend failure.",
    )
