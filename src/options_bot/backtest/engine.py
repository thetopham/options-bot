from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class BacktestResult:
    symbol: str
    trades: list[dict] = field(default_factory=list)
    notes: list[str] = field(default_factory=lambda: ["Backtest engine stub; no profitability claimed."])


class BacktestEngine:
    def run(self, symbol: str) -> BacktestResult:
        return BacktestResult(symbol=symbol)
