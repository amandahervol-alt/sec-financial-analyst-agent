import pytest

from src.financial_agent import SECFinancialAnalystAgent
from tests.conftest import COMPANIES, EXPECTED_METRICS, sample_sections

METRICS = ["revenue", "operating_expenses", "net_income", "eps", "operating_cash_flow"]


@pytest.fixture
def agent():
    return SECFinancialAnalystAgent(api_key="")


@pytest.mark.parametrize("name", sorted(COMPANIES))
@pytest.mark.parametrize("metric", METRICS)
def test_extracts_stated_figures_from_each_sample(agent, name, metric):
    m = agent._extract_financial_metrics(sample_sections(name)["mda"])
    comp = getattr(m, metric)
    assert (comp.current_year_val, comp.prior_year_val) == EXPECTED_METRICS[name][metric]


@pytest.mark.parametrize("name, metric, pct", [
    ("techcorp", "revenue", 22.8),       # matches the filing's stated +22.8%
    ("techcorp", "net_income", 48.8),
    ("healthplus", "revenue", 33.3),
    ("retailhub", "revenue", 14.4),
    ("retailhub", "net_income", 35.3),
])
def test_yoy_change_matches_filing(agent, name, metric, pct):
    assert getattr(agent._extract_financial_metrics(sample_sections(name)["mda"]), metric).yoy_change_pct == pct


def test_extracts_distinct_figures_not_defaults(agent):
    # Distinct from the engine's built-in defaults, so this fails if a regex silently misses.
    mda = (
        "- Revenue: $1,500.0M in FY25 vs $1,000.0M in FY24\n"
        "- Operating Expenses: $700.0M in FY25 vs $800.0M in FY24\n"
        "- Net Income: $55.0M in FY25 vs $50.0M in FY24\n"
        "- Diluted EPS: $1.10 vs $1.00 in FY24\n"
        "- Operating Cash Flow: $99.0M in FY25 vs $90.0M in FY24\n"
    )
    m = agent._extract_financial_metrics(mda)
    assert (m.revenue.current_year_val, m.revenue.prior_year_val) == (1500.0, 1000.0)
    assert m.revenue.yoy_change_pct == 50.0
    assert (m.operating_expenses.current_year_val, m.operating_expenses.prior_year_val) == (700.0, 800.0)
    assert m.operating_expenses.trend == "Negative"
    assert m.operating_expenses.yoy_change_pct == -12.5
    assert (m.eps.current_year_val, m.eps.prior_year_val) == (1.10, 1.00)
    assert m.eps.unit == "$"
    assert m.revenue.unit == "$M"


def test_flat_metric_is_neutral(agent):
    m = agent._extract_financial_metrics("Revenue: $100.0M in FY25 vs $100.0M in FY24")
    assert m.revenue.yoy_change_pct == 0.0
    assert m.revenue.trend == "Neutral"


def test_zero_prior_year_does_not_divide_by_zero(agent):
    m = agent._extract_financial_metrics("Revenue: $100.0M in FY25 vs $0M in FY24")
    assert m.revenue.prior_year_val == 0.0
    assert m.revenue.yoy_change_pct == 0.0


def test_missing_figures_fall_back_to_built_in_defaults(agent):
    # Documents current behavior: unmatched metrics silently use TechCorp's figures.
    m = agent._extract_financial_metrics("No financial figures in this text.")
    assert (m.revenue.current_year_val, m.revenue.prior_year_val) == (1450.0, 1181.0)
    assert (m.eps.current_year_val, m.eps.prior_year_val) == (3.85, 2.60)
