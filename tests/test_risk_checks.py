from options_bot.risk.checks import RiskLimits, evaluate_candidate
from options_bot.strategies.iron_condor import build_iron_condor
from options_bot.strategies.long_strangle import build_long_strangle


def test_risk_rejects_iron_condor_without_protective_wings():
    candidate = build_iron_condor(
        symbol="SPY",
        expiration="2026-06-19",
        short_put_strike=480,
        long_put_strike=475,
        short_call_strike=520,
        long_call_strike=525,
        credit=1.25,
    )
    candidate.legs = [leg for leg in candidate.legs if not (leg.side == "buy" and leg.option_type == "call")]

    decision = evaluate_candidate(candidate, RiskLimits(account_equity=100_000))

    assert not decision.allowed
    assert "protective" in " ".join(decision.reasons).lower()


def test_risk_rejects_options_market_orders():
    candidate = build_long_strangle(
        symbol="SPY",
        expiration="2026-06-19",
        put_strike=480,
        call_strike=520,
        debit=3.40,
    )
    candidate.legs[0].order_type = "market"

    decision = evaluate_candidate(candidate, RiskLimits(account_equity=100_000))

    assert not decision.allowed
    assert "market orders" in " ".join(decision.reasons).lower()


def test_risk_rejects_trade_above_max_risk_fraction():
    candidate = build_iron_condor(
        symbol="SPY",
        expiration="2026-06-19",
        short_put_strike=480,
        long_put_strike=450,
        short_call_strike=520,
        long_call_strike=550,
        credit=1.00,
    )

    decision = evaluate_candidate(candidate, RiskLimits(account_equity=10_000, max_risk_fraction=0.005))

    assert not decision.allowed
    assert "max risk" in " ".join(decision.reasons).lower()
