"""Render an investigation decision as a human-readable explanation."""


def format_explanation(decision: dict) -> str:
    lines = [f"Fraud Score: {decision['fraud_score']:.2f}", "", "Reasons:"]
    for i, reason in enumerate(decision.get("reasons", []), start=1):
        lines.append(f"{i}. {reason}")
    lines += [
        "",
        f"Confidence: {decision.get('confidence', 'low').capitalize()}",
        f"Action: {_action_label(decision.get('action', 'allow'))}",
    ]
    summary = decision.get("summary")
    if summary:
        lines += ["", summary]
    return "\n".join(lines)


def _action_label(action: str) -> str:
    return {
        "allow": "Allow",
        "review": "Hold + Manual Review",
        "block": "Block + Manual Review",
    }.get(action, action)
