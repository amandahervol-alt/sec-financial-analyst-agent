import pytest
from pathlib import Path
from src.sec_parser import SECParser
from src.financial_agent import SECFinancialAnalystAgent
from src.report_generator import ReportGenerator


@pytest.fixture
def sample_10k_text():
    sample_path = Path("data/samples/sample_10k_techcorp.txt")
    if sample_path.exists():
        return sample_path.read_text(encoding="utf-8")
    return """
    ITEM 1. BUSINESS
    TechCorp produces cloud AI software.

    ITEM 1A. RISK FACTORS
    1. Cybersecurity Threats: High risk of data breach.

    ITEM 7. MANAGEMENT'S DISCUSSION AND ANALYSIS (MD&A)
    Revenue: $1,450.0M in FY25 vs $1,181.0M in FY24
    Operating Expenses: $890.0M in FY25 vs $760.0M in FY24
    Net Income: $320.0M in FY25 vs $215.0M in FY24
    EPS: $3.85 vs $2.60
    Operating Cash Flow: $410.0M vs $290.0M
    """


def test_sec_parser(sample_10k_text):
    parser = SECParser(sample_10k_text)
    sections = parser.extract_sections()
    assert "business" in sections
    assert "risk_factors" in sections
    assert "mda" in sections
    assert len(sections["mda"]) > 0


def test_financial_agent_analysis(sample_10k_text):
    parser = SECParser(sample_10k_text)
    sections = parser.extract_sections()

    agent = SECFinancialAnalystAgent()
    report = agent.analyze("TechCorp Solutions Inc.", sections)

    assert report.executive_summary.company_name == "TechCorp Solutions Inc."
    assert report.metrics.revenue.current_year_val == 1450.0
    assert report.metrics.revenue.prior_year_val == 1181.0
    assert report.metrics.revenue.yoy_change_pct == 22.8
    assert report.metrics.net_income.yoy_change_pct == 48.8
    assert len(report.risk_factors) >= 1


def test_report_generator(sample_10k_text):
    parser = SECParser(sample_10k_text)
    sections = parser.extract_sections()
    agent = SECFinancialAnalystAgent()
    report = agent.analyze("TechCorp Solutions Inc.", sections)

    generator = ReportGenerator(report)
    md = generator.generate_markdown()
    html = generator.generate_html()

    assert "# 📈 SEC 10-K Executive Financial Analysis" in md
    assert "<!DOCTYPE html>" in html
    assert "TechCorp Solutions Inc." in html
