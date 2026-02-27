"""
Tool Dispatch Layer — enables agents to autonomously invoke service functions.

Each tool is registered with a name, description, and callable.
Agents call `dispatch_tool(name, **kwargs)` to use any service function
as part of their reasoning loop (Action Capability).
"""
from typing import Callable, Dict, Any, Optional
from services.name_entropy import shannon_entropy, ngram_entropy, has_digits_or_symbols
from services.navigation_consistency_score import click_entropy, navigation_consistency_score
from services.verify_geoip import get_ip_geo_ipinfo, get_ip_geo_ipapi, is_private_ip
from services.verify_email_age_card import check_email_age
from services.sentiment_entity import analyze_company_sentiment
from services.check_id_card import check_id_card
from services.network_signal import get_network_signals

from services.rag_service import (
    fetch_agent_history,
    fetch_orchestrator_history,
    fetch_similar_flags_history,
    store_agent_result,
    store_orchestrator_result,
)


# ─────────────────────────────────────────────────────────────
# Tool Registry
# ─────────────────────────────────────────────────────────────

TOOL_REGISTRY: Dict[str, Dict[str, Any]] = {
    # ── Identity Tools ──────────────────────────────────────
    "shannon_entropy": {
        "fn": shannon_entropy,
        "description": "Calculate Shannon entropy of a name string (0.0-1.0).",
        "agent": "identity_risk_agent",
    },
    "ngram_entropy": {
        "fn": ngram_entropy,
        "description": "Calculate N-gram entropy of a name string (0.0-1.0).",
        "agent": "identity_risk_agent",
    },
    "has_digits_or_symbols": {
        "fn": has_digits_or_symbols,
        "description": "Check if a name contains digits or symbols. Returns bool.",
        "agent": "identity_risk_agent",
    },
    "check_email_age": {
        "fn": check_email_age,
        "description": "Check domain registration age for an email. Returns age in days.",
        "agent": "identity_risk_agent",
    },
    "analyze_company_sentiment": {
        "fn": analyze_company_sentiment,
        "description": "Perform sentiment and risk analysis for a company/entity name.",
        "agent": "identity_risk_agent",
    },
    "get_ip_geo_ipinfo": {
        "fn": get_ip_geo_ipinfo,
        "description": "Get geolocation data for an IP address using ipinfo.io.",
        "agent": "identity_risk_agent",
    },
    "get_ip_geo_ipapi": {
        "fn": get_ip_geo_ipapi,
        "description": "Get geolocation data for an IP address using ip-api.com.",
        "agent": "identity_risk_agent",
    },
    "check_id_card": {
        "fn": check_id_card,
        "description": "OCR and identity verification on KTP image using Qwen VL.",
        "agent": "identity_risk_agent",
    },

    # ── Behavioral Tools ────────────────────────────────────
    "click_entropy": {
        "fn": click_entropy,
        "description": "Calculate entropy of user click positions (0.0-1.0).",
        "agent": "behavioral_agent",
    },
    "navigation_consistency_score": {
        "fn": navigation_consistency_score,
        "description": "Get navigation consistency score for a user from Redis.",
        "agent": "behavioral_agent",
    },

    # ── Network Fraud Tools ─────────────────────────────────
    "get_network_signals": {
        "fn": get_network_signals,
        "description": "Get network fraud signals (shared device/IP counts) from login history.",
        "agent": "synthetic_network_agent",
    },
    "get_ip_geo_ipinfo": {
        "fn": get_ip_geo_ipinfo,
        "description": "Get geolocation data for an IP address using ipinfo.io.",
        "agent": "synthetic_network_agent",
    },
    "get_ip_geo_ipapi": {
        "fn": get_ip_geo_ipapi,
        "description": "Get geolocation data for an IP address using ip-api.com.",
        "agent": "synthetic_network_agent",
    },
    "is_private_ip": {
        "fn": is_private_ip,
        "description": "Check if an IP address is private/internal. Returns bool.",
        "agent": "synthetic_network_agent",
    },

    # ── RAG Tools ───────────────────────────────────────────
    "fetch_agent_history": {
        "fn": fetch_agent_history,
        "description": "Fetch recent historical results for a given agent (RAG).",
        "agent": "all",
    },
    "fetch_orchestrator_history": {
        "fn": fetch_orchestrator_history,
        "description": "Fetch recent orchestrator decisions for RAG.",
        "agent": "all",
    },
    "fetch_similar_flags_history": {
        "fn": fetch_similar_flags_history,
        "description": "Fetch historical cases sharing the same flags.",
        "agent": "all",
    },
    "store_agent_result": {
        "fn": store_agent_result,
        "description": "Store agent result into RAG history table.",
        "agent": "all",
    },
    "store_orchestrator_result": {
        "fn": store_orchestrator_result,
        "description": "Store orchestrator result into RAG history table.",
        "agent": "all",
    },
}


# ─────────────────────────────────────────────────────────────
# Dispatch Functions
# ─────────────────────────────────────────────────────────────

def dispatch_tool(tool_name: str, **kwargs) -> Any:
    """
    Dispatch a tool by name. Returns the tool's result or an error dict.
    This is the primary action capability for all agents.
    """
    if tool_name not in TOOL_REGISTRY:
        return {"error": f"Tool '{tool_name}' not found in registry."}
    try:
        fn = TOOL_REGISTRY[tool_name]["fn"]
        result = fn(**kwargs)
        return result
    except Exception as e:
        return {"error": f"Tool '{tool_name}' failed: {str(e)}"}


async def dispatch_tool_async(tool_name: str, **kwargs) -> Any:
    """
    Dispatch an async tool by name (e.g., check_email_age, analyze_company_sentiment).
    """
    if tool_name not in TOOL_REGISTRY:
        return {"error": f"Tool '{tool_name}' not found in registry."}
    try:
        fn = TOOL_REGISTRY[tool_name]["fn"]
        result = await fn(**kwargs)
        return result
    except Exception as e:
        return {"error": f"Tool '{tool_name}' failed: {str(e)}"}


def get_tools_for_agent(agent_step: str) -> Dict[str, str]:
    """
    Return a dict of tool_name -> description for a specific agent.
    Used to inject available tools into agent prompts.
    """
    tools = {}
    for name, meta in TOOL_REGISTRY.items():
        if meta["agent"] in (agent_step, "all"):
            tools[name] = meta["description"]
    return tools
