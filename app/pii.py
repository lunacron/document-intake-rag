import re
from collections import Counter
from functools import lru_cache

from presidio_analyzer import AnalyzerEngine
from presidio_analyzer.nlp_engine import NlpEngineProvider
from presidio_anonymizer import AnonymizerEngine

# Only high-risk identifiers are redacted. Names, emails, phones, addresses and dates stay
# in the index so staff can ask about a specific student; access to them is controlled by
# role (see auth.py), not by redaction.
ENTITIES = [
    "US_SSN", "US_ITIN", "CREDIT_CARD", "IBAN_CODE", "US_PASSPORT", "US_DRIVER_LICENSE",
]


# Emails are kept on purpose (see above), so a digit run inside one is not an identifier. Without this,
# "kim.wu2007@example.com" had "wu2007" redacted as a driver's license number.
_EMAIL = re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+")


@lru_cache
def _engines() -> tuple[AnalyzerEngine, AnonymizerEngine]:
    nlp = NlpEngineProvider(nlp_configuration={
        "nlp_engine_name": "spacy",
        "models": [{"lang_code": "en", "model_name": "en_core_web_sm"}],
    }).create_engine()
    return AnalyzerEngine(nlp_engine=nlp, supported_languages=["en"]), AnonymizerEngine()


def redact(text: str) -> tuple[str, dict[str, int]]:
    """Replace PII with <ENTITY_TYPE> placeholders. Returns (clean_text, counts)."""
    analyzer, anonymizer = _engines()
    found = analyzer.analyze(text=text, language="en", entities=ENTITIES)
    emails = [m.span() for m in _EMAIL.finditer(text)]
    found = [r for r in found if not any(r.start < e and r.end > b for b, e in emails)]
    if not found:
        return text, {}
    clean = anonymizer.anonymize(text=text, analyzer_results=found).text
    return clean, dict(Counter(r.entity_type for r in found))
