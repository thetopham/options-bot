from options_bot.risk.checks import RiskLimits, evaluate_candidate
from options_bot.strategies.institutional_put_call_overlay import build_institutional_put_call_overlay


def test_build_institutional_put_call_overlay_sells_cash_secured_put_and_buys_otm_call():
    candidate = build_institutional_put_call_overlay(
        symbol="SPY",
        expiration="2026-06-19",
        underlying_price=500.0,
        short_put_strike=470.0,
        long_call_strike=530.0,
        put_credit=6.20,
        call_debit=1.40,
    )

    assert candidate.strategy == "institutional_put_call_overlay"
    assert len(candidate.legs) == 2
    assert candidate.net_credit == 4.80
    assert candidate.max_loss == 46520.0
    assert candidate.max_profit is None
    assert candidate.breakevens == [465.2]
    assert candidate.legs[0].option_type == "put"
    assert candidate.legs[0].side == "sell"
    assert candidate.legs[0].cash_secured is True
    assert candidate.legs[1].option_type == "call"
    assert candidate.legs[1].side == "buy"
    assert candidate.legs[1].strike > 500.0
    assert "cash-secured" in candidate.explanation.lower()
    assert "institution" in candidate.explanation.lower()


def test_risk_allows_cash_secured_short_put_with_otm_call_when_cash_reserved():
    candidate = build_institutional_put_call_overlay(
        symbol="SPY",
        expiration="2026-06-19",
        underlying_price=500.0,
        short_put_strike=470.0,
        long_call_strike=530.0,
        put_credit=6.20,
        call_debit=1.40,
    )

    decision = evaluate_candidate(
        candidate,
        RiskLimits(account_equity=100_000, max_risk_fraction=0.50, require_cash_secured_puts=True),
    )

    assert decision.allowed
    assert decision.reasons == []


def test_risk_rejects_short_put_overlay_when_not_cash_secured():
    candidate = build_institutional_put_call_overlay(
        symbol="SPY",
        expiration="2026-06-19",
        underlying_price=500.0,
        short_put_strike=470.0,
        long_call_strike=530.0,
        put_credit=6.20,
        call_debit=1.40,
        cash_secured=False,
    )

    decision = evaluate_candidate(
        candidate,
        RiskLimits(account_equity=100_000, max_risk_fraction=0.50, require_cash_secured_puts=True),
    )

    assert not decision.allowed
    assert "cash-secured" in " ".join(decision.reasons).lower()
