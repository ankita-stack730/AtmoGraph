"""
Top-level NLP pipeline. Combines entity extraction + disruption
classification into a single structured result (see Section 7 of the spec).
"""
from __future__ import annotations

from app.models.schemas import NLPAnalysisResult
from app.nlp import disruption_detector, entity_extractor


def analyze_text(text: str) -> NLPAnalysisResult:
    entities = entity_extractor.extract_entities(text)
    disruption_type, severity, confidence = disruption_detector.classify(text)

    return NLPAnalysisResult(
        text=text,
        entities=entities,
        disruption_type=disruption_type,
        severity=severity,
        confidence=confidence,
        method="BASELINE_RULE_BASED",
    )
