"""The live-Claude branch, with the Anthropic client mocked."""
import json
import sys
import types
from types import SimpleNamespace
from unittest import mock

import pytest

from src.financial_agent import SECFinancialAnalystAgent
from tests.conftest import sample_sections

VALID_REPORT = {
    "report_title": "SEC 10-K Executive Financial Analysis — Acme",
    "generated_at": "ignored",
    "executive_summary": {
        "company_name": "Acme", "fiscal_year": 2025, "overall_health_score": 8.0,
        "sentiment_label": "Bullish", "key_growth_drivers": ["a"], "management_guidance": "g",
    },
    "metrics": {
        "fiscal_year": 2025, "prior_fiscal_year": 2024,
        **{k: {"metric_name": k, "current_year_val": 2.0, "prior_year_val": 1.0, "yoy_change_pct": 100.0,
               "unit": "$M", "trend": "Positive"}
           for k in ["revenue", "operating_expenses", "net_income", "eps", "operating_cash_flow"]},
    },
    "risk_factors": [{"id": "RISK-01", "title": "t", "category": "General", "severity": "LOW", "summary": "s"}],
}


@pytest.fixture
def fake_anthropic(monkeypatch):
    client = mock.Mock()
    module = types.ModuleType("anthropic")
    module.Anthropic = mock.Mock(return_value=client)
    monkeypatch.setitem(sys.modules, "anthropic", module)
    return client


def _reply(client, text):
    client.messages.create.return_value = SimpleNamespace(content=[SimpleNamespace(type="text", text=text)])


def test_uses_claude_when_key_is_set(fake_anthropic):
    _reply(fake_anthropic, "```json\n" + json.dumps(VALID_REPORT) + "\n```")
    report = SECFinancialAnalystAgent(api_key="sk-test").analyze("Acme", sample_sections("techcorp"))

    assert report.executive_summary.company_name == "Acme"
    assert report.metrics.revenue.current_year_val == 2.0
    assert report.generated_at != "ignored"  # overwritten with a real timestamp
    prompt = fake_anthropic.messages.create.call_args.kwargs["messages"][0]["content"]
    assert "COMPANY: Acme" in prompt and "ITEM 7 MD&A" in prompt


def test_falls_back_to_offline_engine_when_claude_fails(fake_anthropic, capsys):
    fake_anthropic.messages.create.side_effect = RuntimeError("boom")
    report = SECFinancialAnalystAgent(api_key="sk-test").analyze("TechCorp", sample_sections("techcorp"))
    assert report.metrics.revenue.current_year_val == 1450.0
    assert "Falling back to deterministic engine" in capsys.readouterr().out


def test_falls_back_when_claude_returns_invalid_json(fake_anthropic):
    _reply(fake_anthropic, "I cannot help with that.")
    report = SECFinancialAnalystAgent(api_key="sk-test").analyze("HealthPlus", sample_sections("healthplus"))
    assert report.metrics.revenue.current_year_val == 680.0


@pytest.mark.parametrize("key", ["", "your_anthropic_api_key_here"])
def test_placeholder_or_empty_key_never_calls_claude(fake_anthropic, key):
    SECFinancialAnalystAgent(api_key=key).analyze("RetailHub", sample_sections("retailhub"))
    fake_anthropic.messages.create.assert_not_called()


def test_api_key_falls_back_through_env_vars(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "g-key")
    assert SECFinancialAnalystAgent().api_key == "g-key"
    monkeypatch.setenv("ANTHROPIC_API_KEY", "a-key")
    assert SECFinancialAnalystAgent().api_key == "a-key"


def test_reads_first_text_block_after_thinking(fake_anthropic):
    fake_anthropic.messages.create.return_value = SimpleNamespace(content=[
        SimpleNamespace(type="thinking", thinking="let me look at the MD&A"),
        SimpleNamespace(type="text", text=json.dumps(VALID_REPORT)),
    ])
    report = SECFinancialAnalystAgent(api_key="sk-test").analyze("Acme", sample_sections("techcorp"))
    assert report.metrics.revenue.current_year_val == 2.0  # Claude's figure, not the heuristic 1450


def test_no_text_block_falls_back(fake_anthropic):
    fake_anthropic.messages.create.return_value = SimpleNamespace(content=[SimpleNamespace(type="thinking", thinking="...")])
    report = SECFinancialAnalystAgent(api_key="sk-test").analyze("TechCorp", sample_sections("techcorp"))
    assert report.metrics.revenue.current_year_val == 1450.0


def test_request_uses_current_model_without_sampling_params(fake_anthropic):
    _reply(fake_anthropic, json.dumps(VALID_REPORT))
    SECFinancialAnalystAgent(api_key="sk-test").analyze("Acme", sample_sections("techcorp"))
    kwargs = fake_anthropic.messages.create.call_args.kwargs
    assert kwargs["model"] == "claude-sonnet-5-5"
    assert kwargs["max_tokens"] == 4096
    assert kwargs["extra_body"] == {"output_config": {"effort": "low"}}
    assert not {"temperature", "top_p", "top_k"} & kwargs.keys()


def test_model_can_be_overridden(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_MODEL", "claude-sonnet-5")
    assert SECFinancialAnalystAgent(api_key="x").model_name == "claude-sonnet-5"


def test_claude_may_return_null_for_unreported_figures(fake_anthropic):
    data = json.loads(json.dumps(VALID_REPORT))
    data["metrics"]["eps"].update(current_year_val=None, prior_year_val=None, yoy_change_pct=None, trend="Not Reported")
    _reply(fake_anthropic, json.dumps(data))
    report = SECFinancialAnalystAgent(api_key="sk-test").analyze("Acme", sample_sections("techcorp"))
    assert report.metrics.eps.current_display == "N/A"
