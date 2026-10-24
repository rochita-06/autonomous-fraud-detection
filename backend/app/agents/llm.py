"""Anthropic client wrapper. The agent runs on Claude when a key is
available and falls back to the deterministic rule engine otherwise."""

from __future__ import annotations

import os

from ..config import settings

SYSTEM_PROMPT = """You are an autonomous fraud investigator for a payments platform.

You receive one suspicious transaction and must decide: allow, review, or block.

Investigate step by step using your tools:
1. Pull the sender's history to establish a behavioural baseline.
2. Check the transaction against that baseline for anomalies.
3. Query the identity graph for links to flagged accounts and shared devices.
4. Search the fraud-case knowledge base for similar known patterns.

You may call tools in any order and repeat them if a finding needs follow-up
(for example, run get_linked_accounts on a suspicious receiver too). Stop
investigating once your confidence is sufficient — do not call tools whose
output cannot change the decision.

When done, call finalize_decision with:
- fraud_score: 0.0 (certainly legitimate) to 1.0 (certainly fraud)
- confidence: low / medium / high
- reasons: concrete evidence-based bullet points citing numbers from tool
  results (e.g. "Transaction is 5.8x the user's average of $142")
- action: allow (< {review}), review ({review}-{block}), block (>= {block})
- summary: one-paragraph plain-English explanation for a human analyst

Base every reason on actual tool output. Never invent evidence."""


def build_system_prompt() -> str:
    return SYSTEM_PROMPT.replace("{review}", str(settings.fraud_review_threshold)).replace(
        "{block}", str(settings.fraud_block_threshold)
    )


def anthropic_available() -> bool:
    return bool(settings.anthropic_api_key or os.environ.get("ANTHROPIC_API_KEY"))


def get_client():
    import anthropic

    if settings.anthropic_api_key:
        return anthropic.Anthropic(api_key=settings.anthropic_api_key)
    return anthropic.Anthropic()
