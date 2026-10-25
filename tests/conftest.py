import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.sec_parser import SECParser  # noqa: E402

SAMPLES = ROOT / "data" / "samples"

# Figures stated in each sample filing's MD&A: (current, prior)
EXPECTED_METRICS = {
    "techcorp": {
        "revenue": (1450.0, 1181.0), "operating_expenses": (890.0, 760.0), "net_income": (320.0, 215.0),
        "eps": (3.85, 2.60), "operating_cash_flow": (410.0, 290.0),
    },
    "healthplus": {
        "revenue": (680.0, 510.0), "operating_expenses": (490.0, 395.0), "net_income": (145.0, 82.0),
        "eps": (2.15, 1.25), "operating_cash_flow": (210.0, 130.0),
    },
    "retailhub": {
        "revenue": (3250.0, 2840.0), "operating_expenses": (2420.0, 2210.0), "net_income": (460.0, 340.0),
        "eps": (4.20, 3.15), "operating_cash_flow": (680.0, 520.0),
    },
}
COMPANIES = {
    "techcorp": "TechCorp Solutions Inc.",
    "healthplus": "HealthPlus Therapeutics Inc.",
    "retailhub": "RetailHub Global Inc.",
}


@pytest.fixture(autouse=True)
def _offline(monkeypatch):
    """Keep every test offline: no LLM keys, so the deterministic engine runs unless a test opts in."""
    monkeypatch.chdir(ROOT)
    for key in ("ANTHROPIC_API_KEY", "OPENAI_API_KEY", "GEMINI_API_KEY", "ANTHROPIC_MODEL"):
        monkeypatch.delenv(key, raising=False)


def sample_text(name: str) -> str:
    return (SAMPLES / f"sample_10k_{name}.txt").read_text(encoding="utf-8")


def sample_sections(name: str) -> dict:
    return SECParser(sample_text(name)).extract_sections()
