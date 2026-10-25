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


def test_markdown_shows_negative_change_without_plus_sign():
    agent = SECFinancialAnalystAgent(api_key="")
    report = agent._analyze_heuristically("Co", "Operating Expenses: $700.0M in FY25 vs $800.0M in FY24", "")
    md = ReportGenerator(report).generate_markdown()
    assert "| **Operating Expenses** | $800.0M | $700.0M | `-12.5%` | Negative |" in md
    assert "+-" not in md


def test_unreported_metrics_render_as_not_available():
    report = SECFinancialAnalystAgent(api_key="")._analyze_heuristically("Co", "Revenue: $50.0M in FY25 vs $40.0M in FY24", "")
    gen = ReportGenerator(report)
    md = gen.generate_markdown()
    assert "| **Revenue** | $40.0M | $50.0M | `+25.0%` | Positive |" in md
    assert "| **Net Income** | N/A | N/A | `N/A` | Not Reported |" in md
    html = gen.generate_html()
    assert "data: [40.0, null, null, null]" in html
    assert "data: [50.0, null, null, null]" in html
    assert "Not reported" in html and "badge-neutral" in html
    assert "None" not in html


def test_html_badge_direction():
    report = SECFinancialAnalystAgent(api_key="")._analyze_heuristically("Co", "Revenue: $90.0M in FY25 vs $100.0M in FY24", "")
    html = ReportGenerator(report).generate_html()
    assert "▼ -10.0% YoY" in html
    assert "badge-negative" in html
