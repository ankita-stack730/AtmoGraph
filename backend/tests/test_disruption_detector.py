import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.nlp import disruption_detector


def test_port_strike_detected():
    dtype, severity, confidence = disruption_detector.classify(
        "Rotterdam port strike causes major shipping delays."
    )
    assert dtype == "PORT_STRIKE"
    assert 0.0 <= severity <= 1.0
    assert confidence > 0.5


def test_natural_disaster_detected():
    dtype, _, _ = disruption_detector.classify("A severe earthquake damaged the port.")
    assert dtype == "NATURAL_DISASTER"


def test_cyber_attack_detected():
    dtype, _, _ = disruption_detector.classify("The company suffered a ransomware attack.")
    assert dtype == "CYBER_ATTACK"


def test_unknown_text_falls_back_to_default():
    dtype, severity, confidence = disruption_detector.classify("The weather is nice today.")
    assert dtype == disruption_detector.DEFAULT_TYPE
    assert confidence < 0.5


def test_severity_boosted_by_keywords():
    _, severity_plain, _ = disruption_detector.classify("port strike happened")
    _, severity_major, _ = disruption_detector.classify("major port strike happened")
    assert severity_major > severity_plain


def test_severity_and_confidence_bounds():
    for text in [
        "Rotterdam port strike causes major shipping delays.",
        "Factory shutdown after critical fire.",
        "",
    ]:
        if not text:
            continue
        _, severity, confidence = disruption_detector.classify(text)
        assert 0.0 <= severity <= 1.0
        assert 0.0 <= confidence <= 1.0
