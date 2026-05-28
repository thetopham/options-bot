def explain_decision(decision: str, reasons: list[str]) -> str:
    return f"{decision}: " + "; ".join(reasons)
