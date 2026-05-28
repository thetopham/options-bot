from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

OptionType = Literal["call", "put"]
Side = Literal["buy", "sell"]
OrderType = Literal["limit", "market"]


@dataclass
class OptionLeg:
    symbol: str
    expiration: str
    option_type: OptionType
    strike: float
    side: Side
    quantity: int = 1
    order_type: OrderType = "limit"
    bid: float | None = None
    ask: float | None = None
    open_interest: int | None = None
    volume: int | None = None
    delta: float | None = None


@dataclass
class StrategyCandidate:
    symbol: str
    strategy: str
    expiration: str
    legs: list[OptionLeg]
    net_credit: float = 0.0
    net_debit: float = 0.0
    max_profit: float | None = None
    max_loss: float | None = None
    breakevens: list[float] = field(default_factory=list)
    explanation: str = ""
    exit_plan: str = ""
    liquidity_warnings: list[str] = field(default_factory=list)

    @property
    def has_short_options(self) -> bool:
        return any(leg.side == "sell" for leg in self.legs)
