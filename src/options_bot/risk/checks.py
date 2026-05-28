from __future__ import annotations

from dataclasses import dataclass, field

from options_bot.models import OptionLeg, StrategyCandidate


@dataclass
class RiskLimits:
    account_equity: float
    max_risk_fraction: float = 0.01
    max_daily_loss: float = 1_000.0
    max_open_positions: int = 5
    max_bid_ask_spread_fraction: float = 0.20
    min_open_interest: int = 100
    min_volume: int = 10
    kill_switch_active: bool = False
    require_cash_secured_puts: bool = True


@dataclass
class RiskDecision:
    allowed: bool
    reasons: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


def evaluate_candidate(candidate: StrategyCandidate, limits: RiskLimits) -> RiskDecision:
    reasons: list[str] = []
    warnings: list[str] = []
    if limits.kill_switch_active:
        reasons.append("Kill switch is active")
    if any(leg.order_type == "market" for leg in candidate.legs):
        reasons.append("Market orders are rejected for options")
    if candidate.max_loss is None:
        reasons.append("Candidate must define bounded max loss")
    else:
        max_allowed = limits.account_equity * limits.max_risk_fraction
        if candidate.max_loss > max_allowed:
            reasons.append(f"Max risk {candidate.max_loss:.2f} exceeds limit {max_allowed:.2f}")
    reasons.extend(_cash_secured_put_rejections(candidate, limits))
    reasons.extend(_protective_leg_rejections(candidate))
    for leg in candidate.legs:
        if leg.bid is not None and leg.ask is not None and leg.ask > 0:
            midpoint = (leg.bid + leg.ask) / 2
            if midpoint > 0 and (leg.ask - leg.bid) / midpoint > limits.max_bid_ask_spread_fraction:
                reasons.append(f"Bid/ask spread too wide for {leg.option_type} {leg.strike}")
        if leg.open_interest is not None and leg.open_interest < limits.min_open_interest:
            reasons.append(f"Open interest too low for {leg.option_type} {leg.strike}")
        if leg.volume is not None and leg.volume < limits.min_volume:
            warnings.append(f"Volume is low for {leg.option_type} {leg.strike}")
    return RiskDecision(allowed=not reasons, reasons=reasons, warnings=warnings)


def _cash_secured_put_rejections(candidate: StrategyCandidate, limits: RiskLimits) -> list[str]:
    if not limits.require_cash_secured_puts:
        return []
    reasons: list[str] = []
    for leg in candidate.legs:
        if leg.side == "sell" and leg.option_type == "put" and not leg.cash_secured:
            reasons.append(f"Short put {leg.strike} must be cash-secured; naked short puts are rejected")
    return reasons


def _protective_leg_rejections(candidate: StrategyCandidate) -> list[str]:
    reasons: list[str] = []
    for short in [leg for leg in candidate.legs if leg.side == "sell"]:
        if short.option_type == "put" and short.cash_secured:
            continue
        if not _has_protective_long(short, candidate.legs):
            reasons.append(f"Short {short.option_type} {short.strike} has no protective long leg")
    return reasons


def _has_protective_long(short: OptionLeg, legs: list[OptionLeg]) -> bool:
    for leg in legs:
        if leg.side != "buy" or leg.option_type != short.option_type or leg.expiration != short.expiration:
            continue
        if short.option_type == "call" and leg.strike > short.strike:
            return True
        if short.option_type == "put" and leg.strike < short.strike:
            return True
    return False
