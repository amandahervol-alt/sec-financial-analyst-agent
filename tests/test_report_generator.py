import re
from html import escape

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


def _report_with_risk(**risk_fields):
    agent = SECFinancialAnalystAgent(api_key="")
    report = agent.analyze(COMPANIES["techcorp"], sample_sections("techcorp"))
    card = report.risk_factors[0].model_copy(update=risk_fields)
    return report.model_copy(update={"risk_factors": [card, *report.risk_factors[1:]]})


def test_html_escapes_filing_text():
    report = _report_with_risk(title="<script>x()</script>", summary="<img src=x onerror=alert(1)>")
    html = ReportGenerator(report).generate_html()
    assert "<script>x()</script>" not in html
    assert "&lt;script&gt;x()&lt;/script&gt;" in html
    assert "<img src=x" not in html


def test_html_escapes_claude_provided_severity_and_company():
    report = _report_with_risk(severity='HIGH" onmouseover="x()')
    report = report.model_copy(update={"report_title": "Acme </title><script>x()</script>"})
    html = ReportGenerator(report).generate_html()
    assert '" onmouseover="' not in html
    assert "</title><script>" not in html


def test_html_escapes_ampersands_in_sample_text(reports):
    report = reports["retailhub"]
    html = ReportGenerator(report).generate_html()
    for card in report.risk_factors:
        assert escape(card.title) in html


def test_chart_scripts_still_receive_raw_numbers(reports):
    html = ReportGenerator(reports["techcorp"]).generate_html()
    assert "data: [1181.0, 760.0, 215.0, 290.0]" in html
    assert "data: [1450.0, 890.0, 320.0, 410.0]" in html


def test_markdown_keeps_text_unescaped():
    report = _report_with_risk(title="M&A Integration <Risk>")
    assert "### [RISK-01] M&A Integration <Risk>" in ReportGenerator(report).generate_markdown()
