import pytest

from src.financial_agent import SECFinancialAnalystAgent
from tests.conftest import sample_sections


@pytest.fixture
def agent():
    return SECFinancialAnalystAgent(api_key="")


def _cards(agent, name):
    return agent._extract_risk_factors(sample_sections(name)["risk_factors"])


@pytest.mark.parametrize("name", ["techcorp", "healthplus", "retailhub"])
def test_each_sample_has_four_numbered_risks(agent, name):
    cards = _cards(agent, name)
    assert [c.id for c in cards] == ["RISK-01", "RISK-02", "RISK-03", "RISK-04"]
    assert all(not c.title[0].isdigit() for c in cards), "numbering should be stripped from titles"
    assert all(c.severity in {"HIGH", "MEDIUM", "LOW"} for c in cards)


def test_techcorp_risk_titles(agent):
    assert [c.title for c in _cards(agent, "techcorp")] == [
        "Cybersecurity Threats and Data Breaches",
        "Rapid AI Technological Disruption",
        "Foreign Exchange Volatility and Global Macroeconomic Headwinds",
        "Regulatory Compliance and Data Privacy Constraints",
    ]


@pytest.mark.parametrize("name, idx, category, severity", [
    ("techcorp", 0, "Cybersecurity", "HIGH"),
    ("techcorp", 1, "AI & Technology", "MEDIUM"),
    ("techcorp", 2, "Macroeconomic", "MEDIUM"),
    ("techcorp", 3, "Regulatory", "MEDIUM"),   # "Data Privacy" is regulatory, not a breach
    ("healthplus", 1, "Regulatory", "HIGH"),
    ("healthplus", 0, None, "HIGH"),   # "clinical"/"failure" in body -> HIGH
    ("retailhub", 0, "Macroeconomic", "MEDIUM"),
    ("retailhub", 2, "Cybersecurity", "HIGH"),
    ("retailhub", 3, "General", "MEDIUM"),
])
def test_risk_classification(agent, name, idx, category, severity):
    card = _cards(agent, name)[idx]
    if category:
        assert card.category == category
    assert card.severity == severity


@pytest.mark.parametrize("name, idx, expected", [
    ("healthplus", 0, "General"),        # Clinical Trial Failures
    ("healthplus", 3, "Supply Chain"),   # Supply Chain & Biomanufacturing Disruption
    ("retailhub", 1, "Supply Chain"),    # Supply Chain & Freight Logistics Volatility
])
def test_ai_category_does_not_match_inside_words(agent, name, idx, expected):
    assert _cards(agent, name)[idx].category == expected


def test_long_risk_body_is_truncated_to_200_chars(agent):
    card = agent._build_risk_card("RISK-01", "1. Something", "x" * 500)
    assert card.summary == "x" * 200 + "..."
    assert card.title == "Something"


def test_empty_risk_text_returns_default_cards(agent):
    cards = agent._extract_risk_factors("")
    assert [c.id for c in cards] == ["RISK-01", "RISK-02", "RISK-03"]
    assert cards[0].category == "Cybersecurity"


@pytest.mark.parametrize("title, expected", [
    ("Trial Delays", "General"),
    ("Chain Store Closures", "General"),
    ("Retail Competition", "General"),          # "tail" contains "ai"
    ("AI Model Commoditization", "AI & Technology"),
    ("Generative AI Disruption", "AI & Technology"),
    ("Artificial Intelligence Regulation Gaps", "Regulatory"),
    ("Technological Obsolescence", "AI & Technology"),
    ("Ransomware Attacks", "Cybersecurity"),
    ("Data Center Outages", "Cybersecurity"),
    ("Biotech Patent Expiry", "General"),       # "tech" inside a word does not count
])
def test_category_keywords_match_whole_words(agent, title, expected):
    assert agent._build_risk_card("RISK-01", title, "Body text.").category == expected
