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


def test_missing_figures_are_not_reported_instead_of_defaulted(agent):
    # Regression: unmatched metrics used to silently report TechCorp's sample figures.
    m = agent._extract_financial_metrics("No financial figures in this text.")
    for metric in METRICS:
        comp = getattr(m, metric)
        assert comp.current_year_val is None and comp.prior_year_val is None
        assert comp.yoy_change_pct is None
        assert comp.trend == "Not Reported"
        assert not comp.reported
        assert (comp.current_display, comp.change_display) == ("N/A", "N/A")


def test_partially_reported_filing_keeps_found_figures(agent):
    m = agent._extract_financial_metrics("Revenue: $500.0M in FY25 vs $400.0M in FY24")
    assert (m.revenue.current_year_val, m.revenue.yoy_change_pct) == (500.0, 25.0)
    assert m.net_income.current_year_val is None
    assert m.eps.trend == "Not Reported"


@pytest.mark.parametrize("unit, value, expected", [("$M", 12.5, "$12.5M"), ("$", 3.85, "$3.85"), ("%", 4.0, "4.0%")])
def test_value_display_by_unit(unit, value, expected):
    from src.schemas import MetricComparison
    assert MetricComparison(metric_name="x", current_year_val=value, prior_year_val=value, unit=unit).current_display == expected


@pytest.mark.parametrize("pct, expected", [(22.8, "+22.8%"), (-12.5, "-12.5%"), (0.0, "0.0%"), (None, "N/A")])
def test_change_display_signs(pct, expected):
    from src.schemas import MetricComparison
    assert MetricComparison(metric_name="x", yoy_change_pct=pct).change_display == expected
