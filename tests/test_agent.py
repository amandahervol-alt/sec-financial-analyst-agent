import pytest
from pathlib import Path
from src.sec_parser import SECParser
from src.financial_agent import SECFinancialAnalystAgent
from src.report_generator import ReportGenerator

SAMPLE_FILES = [
    ("data/samples/sample_10k_techcorp.txt", "TechCorp Solutions Inc."),
    ("data/samples/sample_10k_healthplus.txt", "HealthPlus Therapeutics Inc."),
    ("data/samples/sample_10k_retailhub.txt", "RetailHub Global Inc.")
]


@pytest.mark.parametrize("file_path,company_name", SAMPLE_FILES)
def test_pipeline_on_all_samples(file_path, company_name):
    path = Path(file_path)
    assert path.exists(), f"Sample file missing: {file_path}"
    raw_text = path.read_text(encoding="utf-8")

    # 1. Test Parser
    parser = SECParser(raw_text)
    sections = parser.extract_sections()
    assert "mda" in sections and len(sections["mda"]) > 0
    assert "risk_factors" in sections and len(sections["risk_factors"]) > 0

    # 2. Test Agent
    agent = SECFinancialAnalystAgent()
    report = agent.analyze(company_name, sections)
    assert report.executive_summary.company_name == company_name
    assert report.metrics.revenue.current_year_val > 0
    assert len(report.risk_factors) >= 1
    assert 1.0 <= report.executive_summary.overall_health_score <= 10.0

    # 3. Test Report Generator
    generator = ReportGenerator(report)
    md = generator.generate_markdown()
    html = generator.generate_html()

    assert f"SEC 10-K Executive Financial Analysis — {company_name}" in md
    assert "<!DOCTYPE html>" in html
    assert "financialsChart" in html
    assert "riskChart" in html
