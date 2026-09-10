"""
Disruption classification — BASELINE implementation.

This is deterministic keyword matching, explicitly NOT a trained classifier.
It exists so the pipeline produces a usable disruption_type + severity before
any ML model is available. See Section 7 / Section 17 of the spec.
"""
from __future__ import annotations

from typing import Dict, List, Tuple

# Ordered so more specific types are checked before generic ones.
DISRUPTION_KEYWORDS: Dict[str, List[str]] = {
    "PORT_STRIKE": ["port strike", "dockworker strike", "port workers strike", "longshoremen strike"],
    "CYBER_ATTACK": ["cyberattack", "cyber attack", "ransomware", "data breach", "hacked"],
    "WAR_CONFLICT": ["war", "conflict", "military strike", "invasion", "attack on", "blockade"],
    "NATURAL_DISASTER": [
        "earthquake", "flood", "hurricane", "typhoon", "tsunami", "wildfire",
        "storm", "cyclone", "volcanic",
    ],
    "FACTORY_SHUTDOWN": ["factory shutdown", "plant closure", "production halt", "factory fire", "plant shutdown"],
    "SUPPLIER_FAILURE": ["supplier bankruptcy", "supplier failure", "insolvency", "bankrupt", "supplier collapse"],
    "SHIPPING_DELAY": ["shipping delay", "vessel delay", "container backlog", "port congestion"],
    "TRANSPORT_DISRUPTION": [
        "shipping delays", "transport disruption", "logistics disruption", "route closure",
        "delivery delay", "delays",
    ],
}

# Keywords that push severity up regardless of type.
SEVERITY_BOOST_KEYWORDS = {
    "major": 0.15,
    "severe": 0.2,
    "critical": 0.25,
    "massive": 0.2,
    "complete shutdown": 0.25,
    "indefinite": 0.15,
}

BASE_SEVERITY = 0.5
DEFAULT_TYPE = "TRANSPORT_DISRUPTION"


def classify(text: str) -> Tuple[str, float, float]:
    """Returns (disruption_type, severity[0-1], confidence[0-1])."""
    lowered = text.lower()

    matched_type = None
    matched_keyword_count = 0

    for disruption_type, keywords in DISRUPTION_KEYWORDS.items():
        hits = [kw for kw in keywords if kw in lowered]
        if hits:
            matched_type = disruption_type
            matched_keyword_count = len(hits)
            break  # dict order = priority order

    if matched_type is None:
        # No confident match — fall back to a generic type with low confidence.
        return DEFAULT_TYPE, BASE_SEVERITY, 0.3

    severity = BASE_SEVERITY + 0.1 * matched_keyword_count
    for boost_kw, boost_val in SEVERITY_BOOST_KEYWORDS.items():
        if boost_kw in lowered:
            severity += boost_val

    severity = max(0.0, min(1.0, severity))
    confidence = 0.9 if matched_keyword_count > 1 else 0.75

    return matched_type, round(severity, 2), confidence
