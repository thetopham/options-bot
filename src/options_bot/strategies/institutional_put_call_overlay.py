from __future__ import annotations

from options_bot.models import OptionLeg, StrategyCandidate

CONTRACT_MULTIPLIER = 100


def build_institutional_put_call_overlay(
    *,
    symbol: str,
    expiration: str,
    underlying_price: float,
    short_put_strike: float,
    long_call_strike: float,
    put_credit: float,
    call_debit: float,
    cash_secured: bool = True,
) -> StrategyCandidate:
    """Build a cash-secured short-put plus OTM long-call overlay.

    Framing: the bot is willing to provide downside liquidity by selling a
    cash-secured put, while using some of the premium to buy convex upside via
    an out-of-the-money call. This is paper/research only; the phrase
    "institutions" is represented as a liquidity-taking counterparty, not a
    guaranteed fill source or edge claim.
    """
    if short_put_strike >= underlying_price:
        raise ValueError("Short put must be below the underlying price")
    if long_call_strike <= underlying_price:
        raise ValueError("Long call must be out-of-the-money above the underlying price")
    if put_credit <= 0:
        raise ValueError("Put credit must be positive")
    if call_debit < 0:
        raise ValueError("Call debit cannot be negative")

    net_credit = round(put_credit - call_debit, 2)
    if net_credit < 0:
        max_loss = round((short_put_strike + abs(net_credit)) * CONTRACT_MULTIPLIER, 2)
    else:
        max_loss = round((short_put_strike - net_credit) * CONTRACT_MULTIPLIER, 2)
    breakeven = round(short_put_strike - net_credit, 2)

    legs = [
        OptionLeg(
            symbol=symbol,
            expiration=expiration,
            option_type="put",
            strike=short_put_strike,
            side="sell",
            cash_secured=cash_secured,
        ),
        OptionLeg(
            symbol=symbol,
            expiration=expiration,
            option_type="call",
            strike=long_call_strike,
            side="buy",
        ),
    ]
    return StrategyCandidate(
        symbol=symbol,
        strategy="institutional_put_call_overlay",
        expiration=expiration,
        legs=legs,
        net_credit=max(net_credit, 0.0),
        net_debit=abs(net_credit) if net_credit < 0 else 0.0,
        max_profit=None,
        max_loss=max_loss,
        breakevens=[breakeven],
        explanation=(
            "Cash-secured put/call overlay: sell a cash-secured OTM put to provide "
            "downside liquidity to institutional-style counterparties, then use part "
            "of the premium to buy an OTM call for convex upside. Paper/research only; "
            "no claim of preferential institutional flow or profitability."
        ),
        exit_plan=(
            "Exit or roll the short put if assignment risk, trend break, or max-loss "
            "threshold is reached; take profits or trail the OTM call on upside expansion; "
            "close before expiration unless assignment is explicitly approved in paper mode."
        ),
    )
