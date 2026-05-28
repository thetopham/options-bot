from __future__ import annotations

from options_bot.execution.order_builder import MultiLegOrderIntent


def submit_paper_order(intent: MultiLegOrderIntent, trading_client):
    if not intent.submit:
        return {"submitted": False, "reason": "dry_run", "intent": intent}
    # Placeholder: map intent to alpaca-py multi-leg request once credentials and paper account are configured.
    raise NotImplementedError("Paper submission adapter is intentionally not wired in scaffold")
