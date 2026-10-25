import pytest

from src.financial_agent import SECFinancialAnalystAgent
from tests.conftest import COMPANIES, sample_sections


def _metrics_with_revenue_change(agent, curr, prior):
    return agent._extract_financial_metrics(f"Revenue: ${curr}M in FY25 vs ${prior}M in FY24")


@pytest.mark.parametrize("curr, prior, score, label", [
    (130.0, 100.0, 10.0, "Strong Bullish"),  # +30% -> 7 + 3 = 10 (capped)
    (115.0, 100.0, 8.5, "Bullish"),          # +15%
    (105.0, 100.0, 7.5, "Neutral"),          # +5%
    (100.0, 100.0, 7.0, "Neutral"),          # 0%
    (90.0, 100.0, 6.0, "Bearish"),           # -10%
    (10.0, 100.0, 1.0, "Bearish"),           # -90% -> floored at 1.0
])
def test_health_score_and_sentiment(curr, prior, score, label):
    agent = SECFinancialAnalystAgent(api_key="")
    summary = agent._generate_executive_summary("Co", "", _metrics_with_revenue_change(agent, curr, prior))
    assert summary.overall_health_score == score
    assert summary.sentiment_label == label


@pytest.mark.parametrize("name, score, label", [
    ("techcorp", 9.3, "Strong Bullish"),
    ("healthplus", 10.0, "Strong Bullish"),
    ("retailhub", 8.4, "Bullish"),
])
def test_sample_reports(name, score, label):
    report = SECFinancialAnalystAgent(api_key="").analyze(COMPANIES[name], sample_sections(name))
    e = report.executive_summary
    assert (e.overall_health_score, e.sentiment_label) == (score, label)
    assert e.company_name == COMPANIES[name]
    assert e.fiscal_year == 2025
    assert len(e.key_growth_drivers) == 3
    assert "FY2026" in e.management_guidance
