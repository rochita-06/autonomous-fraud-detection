"""The autonomous investigation agent (LangGraph).

Graph:  planner -> tools -> planner -> ... -> decide -> END

Two interchangeable engines drive the planner:
  - "claude": Claude decides which tools to call and when to stop
    (think -> act -> observe loop, ends by calling finalize_decision)
  - "rules":  deterministic plan + weighted scoring (no API key needed)
"""

from __future__ import annotations

import json
from typing import Any, TypedDict

from langgraph.graph import END, StateGraph

from ..config import settings
from ..tools.registry import TOOL_SPECS, execute_tool
from .llm import anthropic_available, build_system_prompt, get_client
from .scoring import score_from_results

FINALIZE_SPEC = {
    "name": "finalize_decision",
    "description": "Submit your final fraud decision once the investigation is complete.",
    "input_schema": {
        "type": "object",
        "properties": {
            "fraud_score": {"type": "number", "description": "0.0 to 1.0"},
            "confidence": {"type": "string", "enum": ["low", "medium", "high"]},
            "reasons": {"type": "array", "items": {"type": "string"}},
            "action": {"type": "string", "enum": ["allow", "review", "block"]},
            "summary": {"type": "string"},
        },
        "required": ["fraud_score", "confidence", "reasons", "action", "summary"],
    },
}

RULES_PLAN = [
    "get_user_history",
    "check_transaction_pattern",
    "get_linked_accounts",
    "search_similar_cases",
]


class AgentState(TypedDict, total=False):
    transaction: dict
    engine: str                 # "claude" | "rules"
    messages: list[Any]         # anthropic conversation (claude engine)
    plan_queue: list[str]       # remaining tools (rules engine)
    pending_calls: list[dict]   # tool calls chosen by the planner
    tool_results: dict          # tool name -> latest result
    reasoning_log: list[dict]
    decision: dict | None
    steps: int
    force_finalize: bool


def _log(state: AgentState, entry: dict) -> list[dict]:
    log = list(state.get("reasoning_log", []))
    entry["step"] = len(log) + 1
    log.append(entry)
    return log


def _rules_args(tool: str, state: AgentState) -> dict:
    tx = state["transaction"]
    if tool == "get_user_history":
        return {"user_id": tx.get("user_id", "")}
    if tool == "check_transaction_pattern":
        return {"tx": tx}
    if tool == "get_linked_accounts":
        return {"user_id": tx.get("user_id", "")}
    if tool == "search_similar_cases":
        pattern = state.get("tool_results", {}).get("check_transaction_pattern", {})
        anomalies = " ".join(pattern.get("anomalies", []))
        return {"query": (
            f"{tx.get('merchant_category', 'payment')} transaction of ${tx.get('amount')} "
            f"{pattern.get('amount_ratio_vs_avg', 1)}x above average {anomalies} "
            f"to receiver {tx.get('receiver_id', 'unknown')}"
        ).strip()}
    return {}


# ---------------------------------------------------------------- planner

def planner(state: AgentState) -> dict:
    if state["engine"] == "claude":
        try:
            return _claude_planner(state)
        except Exception as e:  # API/network failure -> degrade gracefully
            log = _log(state, {
                "type": "thought",
                "content": f"Claude engine unavailable ({type(e).__name__}) — "
                           f"switching to rule-based engine",
            })
            done = set(state.get("tool_results", {}))
            return {
                "engine": "rules",
                "plan_queue": [t for t in RULES_PLAN if t not in done],
                "reasoning_log": log,
            }
    return _rules_planner(state)


def _rules_planner(state: AgentState) -> dict:
    queue = list(state.get("plan_queue", []))
    if not queue:
        return {"pending_calls": [], "reasoning_log": _log(state, {
            "type": "thought",
            "content": "All planned checks complete — computing weighted fraud score.",
        })}
    tool = queue.pop(0)
    thoughts = {
        "get_user_history": "Establish the sender's behavioural baseline.",
        "check_transaction_pattern": "Compare this transaction against the baseline for anomalies.",
        "get_linked_accounts": "Check the identity graph for links to flagged accounts and shared devices.",
        "search_similar_cases": "Search the knowledge base for similar known fraud patterns.",
    }
    return {
        "plan_queue": queue,
        "pending_calls": [{"id": tool, "name": tool, "input": _rules_args(tool, state)}],
        "reasoning_log": _log(state, {"type": "thought", "content": thoughts.get(tool, tool)}),
        "steps": state.get("steps", 0) + 1,
    }


def _claude_planner(state: AgentState) -> dict:
    client = get_client()
    steps = state.get("steps", 0)
    force = state.get("force_finalize", False) or steps >= settings.agent_max_steps

    kwargs: dict[str, Any] = dict(
        model=settings.anthropic_model,
        max_tokens=16000,
        system=build_system_prompt(),
        tools=TOOL_SPECS + [FINALIZE_SPEC],
        messages=state["messages"],
    )
    if force:
        kwargs["tool_choice"] = {"type": "tool", "name": "finalize_decision"}
    else:
        kwargs["thinking"] = {"type": "adaptive"}

    response = client.messages.create(**kwargs)

    log = state.get("reasoning_log", [])
    tmp_state = dict(state)
    for block in response.content:
        if block.type == "text" and block.text.strip():
            log = _log({**tmp_state, "reasoning_log": log}, {"type": "thought", "content": block.text.strip()})

    tool_calls = [b for b in response.content if b.type == "tool_use"]
    finalize = next((c for c in tool_calls if c.name == "finalize_decision"), None)
    if finalize:
        return {
            "decision": dict(finalize.input),
            "pending_calls": [],
            "reasoning_log": log,
            "steps": steps + 1,
        }

    if not tool_calls:
        # Model answered in prose without finalizing — force it next round.
        return {
            "messages": state["messages"] + [
                {"role": "assistant", "content": response.content},
                {"role": "user", "content": "Call finalize_decision now with your conclusion."},
            ],
            "force_finalize": True,
            "pending_calls": [],
            "reasoning_log": log,
            "steps": steps + 1,
        }

    return {
        "messages": state["messages"] + [{"role": "assistant", "content": response.content}],
        "pending_calls": [
            {"id": c.id, "name": c.name, "input": dict(c.input)} for c in tool_calls
        ],
        "reasoning_log": log,
        "steps": steps + 1,
    }


# ---------------------------------------------------------------- tools

def run_tools(state: AgentState) -> dict:
    results = dict(state.get("tool_results", {}))
    log = state.get("reasoning_log", [])
    result_blocks = []

    for call in state.get("pending_calls", []):
        output = execute_tool(call["name"], call["input"])
        results[call["name"]] = output
        log = _log({**state, "reasoning_log": log}, {
            "type": "tool_call", "tool": call["name"],
            "input": call["input"], "output": output,
        })
        result_blocks.append({
            "type": "tool_result",
            "tool_use_id": call["id"],
            "content": json.dumps(output, default=str),
        })

    update: dict = {"tool_results": results, "reasoning_log": log, "pending_calls": []}
    if state["engine"] == "claude":
        update["messages"] = state["messages"] + [{"role": "user", "content": result_blocks}]
    return update


# ---------------------------------------------------------------- decide

def decide(state: AgentState) -> dict:
    decision = state.get("decision")
    if decision is None:
        decision = score_from_results(state["transaction"], state.get("tool_results", {}))
    decision["fraud_score"] = max(0.0, min(1.0, float(decision.get("fraud_score", 0))))
    log = _log(state, {"type": "decision", "content": decision})
    return {"decision": decision, "reasoning_log": log}


# ---------------------------------------------------------------- graph

def _route_after_planner(state: AgentState) -> str:
    if state.get("decision") is not None:
        return "decide"
    if state.get("pending_calls"):
        return "tools"
    if state["engine"] == "rules" and not state.get("plan_queue"):
        return "decide"
    return "planner" if state.get("force_finalize") else "decide"


def build_agent():
    graph = StateGraph(AgentState)
    graph.add_node("planner", planner)
    graph.add_node("tools", run_tools)
    graph.add_node("decide", decide)
    graph.set_entry_point("planner")
    graph.add_conditional_edges("planner", _route_after_planner,
                                {"tools": "tools", "decide": "decide", "planner": "planner"})
    graph.add_edge("tools", "planner")
    graph.add_edge("decide", END)
    return graph.compile()


_agent = None


def investigate(transaction: dict) -> dict:
    """Run a full investigation. Returns decision + reasoning log + engine used."""
    global _agent
    if _agent is None:
        _agent = build_agent()

    engine = "claude" if anthropic_available() else "rules"
    initial: AgentState = {
        "transaction": transaction,
        "engine": engine,
        "messages": [{
            "role": "user",
            "content": "Investigate this transaction:\n" + json.dumps(transaction, default=str),
        }],
        "plan_queue": list(RULES_PLAN),
        "pending_calls": [],
        "tool_results": {},
        "reasoning_log": [],
        "decision": None,
        "steps": 0,
        "force_finalize": False,
    }
    final = _agent.invoke(initial, {"recursion_limit": 50})
    return {
        "decision": final["decision"],
        "reasoning_log": final["reasoning_log"],
        "tool_results": final.get("tool_results", {}),
        "engine": final["engine"],
    }
