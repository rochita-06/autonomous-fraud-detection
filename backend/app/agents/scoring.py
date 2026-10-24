"""Deterministic fraud scoring from tool results.

This is the fallback decision engine (no API key needed) and also documents
exactly which signals feed the score, which keeps the system explainable.
"""

from __future__ import annotations

from ..config import settings

ANOMALY_WEIGHTS = {
    "amount_far_above_average": 0.20,
    "amount_above_average": 0.10,
    "unusual_country": 0.12,
    "odd_hour": 0.08,
    "high_risk_category": 0.12,
    "round_amount": 0.05,
    "high_velocity": 0.15,
}


def score_from_results(tx: dict, results: dict) -> dict:
    score = 0.0
    reasons: list[str] = []

    history = results.get("get_user_history", {})
    pattern = results.get("check_transaction_pattern", {})
    graph = results.get("get_linked_accounts", {})
    cases = results.get("search_similar_cases", {})

    if history.get("is_flagged"):
        score += 0.30
        reasons.append("Sender account is already flagged for prior fraud")
    if not history.get("found", True):
        score += 0.15
        reasons.append("Sender has no history on file (unknown account)")

    ratio = pattern.get("amount_ratio_vs_avg")
    for anomaly in pattern.get("anomalies", []):
        score += ANOMALY_WEIGHTS.get(anomaly, 0.05)
    if ratio and ratio >= 1.8:
        reasons.append(
            f"Transaction is {ratio}x the sender's average of ${pattern.get('user_avg_amount')}"
        )
    if "unusual_country" in pattern.get("anomalies", []):
        reasons.append(f"Transaction from {tx.get('country')} — outside the sender's usual countries")
    if "odd_hour" in pattern.get("anomalies", []):
        reasons.append(f"Initiated at an unusual hour ({pattern.get('hour')}:00)")
    if "high_risk_category" in pattern.get("anomalies", []):
        reasons.append(f"High-risk merchant category: {tx.get('merchant_category')}")
    if "high_velocity" in pattern.get("anomalies", []):
        reasons.append(
            f"{pattern.get('recent_tx_count_10min')} transactions from this account in the last 10 minutes"
        )

    flagged_links = graph.get("flagged_connection_count", 0)
    if flagged_links:
        score += min(0.15 + 0.08 * flagged_links, 0.35)
        reasons.append(
            f"Graph link to {flagged_links} flagged account(s): "
            f"{', '.join(graph.get('flagged_connections', [])[:4])}"
        )
    shared = graph.get("shared_devices", [])
    heavily_shared = [d for d in shared if len(d.get("shared_with", [])) >= 2]
    if heavily_shared:
        score += 0.10
        d = heavily_shared[0]
        reasons.append(
            f"Device {d['device_id']} is shared with {len(d['shared_with'])} other accounts"
        )

    matches = cases.get("matches", [])
    if matches and matches[0]["similarity"] >= 0.35:
        top = matches[0]
        score += 0.15
        reasons.append(
            f"Matches known fraud pattern '{top['fraud_type']}' "
            f"(case {top['case_id']}, similarity {top['similarity']:.2f})"
        )

    score = round(min(score, 0.99), 2)

    if score >= settings.fraud_block_threshold:
        action = "block"
    elif score >= settings.fraud_review_threshold:
        action = "review"
    else:
        action = "allow"

    strong_signals = len(reasons)
    if strong_signals >= 3 or score >= 0.85 or score <= 0.15:
        confidence = "high"
    elif strong_signals == 2:
        confidence = "medium"
    else:
        confidence = "low"

    if not reasons:
        reasons.append("No significant anomalies against the sender's baseline")

    summary = (
        f"Transaction {tx.get('tx_id', '')} for ${tx.get('amount')} by {tx.get('user_id')} "
        f"scored {score} ({confidence} confidence). "
        + ("Key signals: " + "; ".join(reasons[:3]) + ". " if score > 0.15 else "")
        + f"Recommended action: {action}."
    )

    return {
        "fraud_score": score,
        "confidence": confidence,
        "reasons": reasons,
        "action": action,
        "summary": summary,
    }
