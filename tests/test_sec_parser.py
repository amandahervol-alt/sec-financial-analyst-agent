import pytest

from src.sec_parser import SECParser
from tests.conftest import COMPANIES, sample_sections


@pytest.mark.parametrize("name", sorted(COMPANIES))
def test_extracts_all_three_sections_from_samples(name):
    sections = sample_sections(name)
    assert set(sections) == {"business", "risk_factors", "mda"}
    assert all(sections.values()), f"empty section in {name}: {[k for k, v in sections.items() if not v]}"


@pytest.mark.parametrize("name", sorted(COMPANIES))
def test_sections_do_not_bleed_into_each_other(name):
    s = sample_sections(name)
    assert "ITEM 1A" not in s["business"].upper()
    assert "ITEM 7" not in s["risk_factors"].upper()
    assert "RISK FACTORS" not in s["mda"].upper()
    assert "Revenue" in s["mda"]
    assert "1." in s["risk_factors"]


def test_business_section_content():
    assert sample_sections("techcorp")["business"].startswith("TechCorp Solutions Inc. is a leading enterprise cloud")


def test_markers_are_case_insensitive():
    text = "item 1. business\nWe sell widgets.\nitem 1a. risk factors\nRisky.\nitem 7. management's discussion and analysis\nRevenue up."
    s = SECParser(text).extract_sections()
    assert s["business"] == "We sell widgets."
    assert s["risk_factors"] == "Risky."
    assert "Revenue up." in s["mda"]


def test_risk_factors_end_at_item_1b_when_item_7_is_missing():
    text = "ITEM 1A. RISK FACTORS\nRisk one.\nITEM 1B. UNRESOLVED STAFF COMMENTS\nNone."
    assert SECParser(text).extract_sections()["risk_factors"] == "Risk one."


def test_mda_stops_at_item_7a():
    text = "ITEM 7. MANAGEMENT'S DISCUSSION AND ANALYSIS\nRevenue grew.\nITEM 7A. QUANTITATIVE DISCLOSURES\nMarket risk."
    mda = SECParser(text).extract_sections()["mda"]
    assert "Revenue grew." in mda
    assert "Market risk." not in mda


def test_unstructured_text_falls_back_to_first_4000_chars_as_mda():
    text = "No item headers here. " * 500
    s = SECParser(text).extract_sections()
    assert s["mda"] == text[:4000]
    assert s["business"] == "" and s["risk_factors"] == ""
