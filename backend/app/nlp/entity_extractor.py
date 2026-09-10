"""
Entity extraction — BASELINE implementation.

Uses spaCy's small English pipeline (en_core_web_sm) for general NER
(locations, organizations, etc.) plus a small supply-chain gazetteer to catch
domain terms spaCy's general-purpose model often misses (e.g. "port",
"warehouse"). This is a rule-assisted baseline, not a fine-tuned domain
model — see Section 7 of the spec.
"""
from __future__ import annotations

import logging
from functools import lru_cache
from typing import List

import spacy

from app.models.schemas import ExtractedEntity

logger = logging.getLogger("atmograph.nlp.entities")

# spaCy label -> our normalized entity type
SPACY_LABEL_MAP = {
    "GPE": "LOCATION",
    "LOC": "LOCATION",
    "ORG": "ORGANIZATION",
    "FAC": "FACILITY",
    "NORP": "GROUP",
    "PRODUCT": "PRODUCT",
}

# Small domain gazetteer (case-insensitive substring match) for terms that
# generic NER frequently misses or mislabels. Extend this as needed.
SUPPLY_CHAIN_GAZETTEER = {
    "port": "PORT",
    "warehouse": "WAREHOUSE",
    "shipping route": "SHIPPING_ROUTE",
    "factory": "FACILITY",
    "plant": "FACILITY",
    "supplier": "SUPPLIER",
    "manufacturer": "MANUFACTURER",
}


@lru_cache
def _load_model():
    try:
        return spacy.load("en_core_web_sm")
    except OSError as exc:  # model not downloaded
        raise RuntimeError(
            "spaCy model 'en_core_web_sm' is not installed. Run: "
            "python -m spacy download en_core_web_sm"
        ) from exc


def extract_entities(text: str) -> List[ExtractedEntity]:
    """Extract named entities from free text.

    Returns a de-duplicated list of ExtractedEntity, combining spaCy NER
    output with gazetteer keyword hits.
    """
    nlp = _load_model()
    doc = nlp(text)

    entities: List[ExtractedEntity] = []
    seen = set()

    for ent in doc.ents:
        entity_type = SPACY_LABEL_MAP.get(ent.label_)
        if entity_type is None:
            continue
        key = (ent.text.lower(), entity_type)
        if key in seen:
            continue
        seen.add(key)
        entities.append(
            ExtractedEntity(
                text=ent.text,
                type=entity_type,
                start_char=ent.start_char,
                end_char=ent.end_char,
            )
        )

    lowered = text.lower()
    for phrase, entity_type in SUPPLY_CHAIN_GAZETTEER.items():
        idx = lowered.find(phrase)
        if idx == -1:
            continue
        key = (phrase, entity_type)
        if key in seen:
            continue
        seen.add(key)
        entities.append(
            ExtractedEntity(
                text=text[idx: idx + len(phrase)],
                type=entity_type,
                start_char=idx,
                end_char=idx + len(phrase),
            )
        )

    return entities
