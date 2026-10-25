import re

import pytest

from src.financial_agent import SECFinancialAnalystAgent
from src.report_generator import ReportGenerator
from tests.conftest import COMPANIES, sample_sections


@pytest.fixture(scope="module")
def reports():
    agent = SECFinancialAnalystAgent(api_key="")
    return {n: agent.analyze(COMPANIES[n], sample_sections(n)) for n in COMPANIES}


@pytest.mark.parametrize("name", sorted(COMPANIES))
def test_markdown_contains_title_metrics_and_risks(reports, name):
    report = reports[name]
    md = ReportGenerator(report).generate_markdown()
    assert md.startswith(f"# 📈 SEC 10-K Executive Financial Analysis — {COMPANIES[name]}")
    assert f"${report.metrics.revenue.current_year_val}M" in md
    assert "| Metric | FY2024 | FY2025 |" in md
    for card in report.risk_factors:
        assert f"### [{card.id}] {card.title}" in md


@pytest.mark.parametrize("name", sorted(COMPANIES))
def test_html_dashboard_embeds_chart_data(reports, name):
    report = reports[name]
    html = ReportGenerator(report).generate_html()
    assert html.lstrip().startswith("<!DOCTYPE html>")
    assert 'id="financialsChart"' in html and 'id="riskChart"' in html
    m = report.metrics
    assert f"{m.revenue.current_year_val}, {m.operating_expenses.current_year_val}" in html
    high = sum(c.severity == "HIGH" for c in report.risk_factors)
    med = sum(c.severity == "MEDIUM" for c in report.risk_factors)
    assert re.search(rf"data:\s*\[{high},\s*{med},\s*0\]", html)
    assert "{{" not in html, "unrendered Jinja placeholder"


@pytest.mark.xfail(strict=True, reason="Known bug: markdown hardcodes '+' so declines render as '+-12.5%'")
def test_markdown_shows_negative_change_without_plus_sign():
    agent = SECFinancialAnalystAgent(api_key="")
    metrics = agent._extract_financial_metrics("Operating Expenses: $700.0M in FY25 vs $800.0M in FY24")
    report = agent._analyze_heuristically("Co", "Operating Expenses: $700.0M in FY25 vs $800.0M in FY24", "")
    assert metrics.operating_expenses.yoy_change_pct == -12.5
    assert "+-" not in ReportGenerator(report).generate_markdown()
