from options_bot.strategies.iron_condor import build_iron_condor
from options_bot.strategies.long_strangle import build_long_strangle


def test_build_iron_condor_has_four_legs_defined_risk_and_explanation():
    candidate = build_iron_condor(
        symbol="SPY",
        expiration="2026-06-19",
        short_put_strike=480,
        long_put_strike=475,
        short_call_strike=520,
        long_call_strike=525,
        credit=1.25,
    )

    assert candidate.strategy == "iron_condor"
    assert len(candidate.legs) == 4
    assert candidate.max_profit == 125.0
    assert candidate.max_loss == 375.0
    assert candidate.breakevens == [478.75, 521.25]
    assert "range" in candidate.explanation.lower()
    assert all(leg.order_type == "limit" for leg in candidate.legs)


def test_build_long_strangle_has_two_long_legs_bounded_debit_and_explanation():
    candidate = build_long_strangle(
        symbol="SPY",
        expiration="2026-06-19",
        put_strike=480,
        call_strike=520,
        debit=3.40,
    )

    assert candidate.strategy == "long_strangle"
    assert len(candidate.legs) == 2
    assert candidate.max_loss == 340.0
    assert candidate.max_profit is None
    assert candidate.breakevens == [476.6, 523.4]
    assert "vol" in candidate.explanation.lower()
    assert all(leg.side == "buy" for leg in candidate.legs)
