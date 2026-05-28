from __future__ import annotations

from options_bot.models import OptionLeg, StrategyCandidate

CONTRACT_MULTIPLIER = 100


def build_iron_condor(
    *,
    symbol: str,
    expiration: str,
    short_put_strike: float,
    long_put_strike: float,
    short_call_strike: float,
    long_call_strike: float,
    credit: float,
) -> StrategyCandidate:
    if not (long_put_strike < short_put_strike < short_call_strike < long_call_strike):
        raise ValueError("Iron condor strikes must be long_put < short_put < short_call < long_call")
    put_width = short_put_strike - long_put_strike
    call_width = long_call_strike - short_call_strike
    if put_width != call_width:
        raise ValueError("Initial scaffold requires symmetric wing widths for clear max-loss math")
    max_profit = round(credit * CONTRACT_MULTIPLIER, 2)
    max_loss = round((put_width - credit) * CONTRACT_MULTIPLIER, 2)
    legs = [
        OptionLeg(symbol, expiration, "put", long_put_strike, "buy"),
        OptionLeg(symbol, expiration, "put", short_put_strike, "sell"),
        OptionLeg(symbol, expiration, "call", short_call_strike, "sell"),
        OptionLeg(symbol, expiration, "call", long_call_strike, "buy"),
    ]
    return StrategyCandidate(
        symbol=symbol,
        strategy="iron_condor",
        expiration=expiration,
        legs=legs,
        net_credit=credit,
        max_profit=max_profit,
        max_loss=max_loss,
        breakevens=[round(short_put_strike - credit, 2), round(short_call_strike + credit, 2)],
        explanation=(
            "Iron condor candidate: sell expensive implied volatility/fear when the underlying "
            "is expected to remain in a defined range; all short legs have protective wings."
        ),
        exit_plan="Take profit at 40-60% max profit; stop at 1.5-2x credit loss; close before expiration.",
    )
