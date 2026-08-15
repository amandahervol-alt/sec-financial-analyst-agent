import re
from typing import Dict


class SECParser:
    """Parser to chunk and extract specific items from SEC 10-K filings."""

    def __init__(self, raw_text: str):
        self.raw_text = raw_text

    def extract_sections(self) -> Dict[str, str]:
        """Extract Item 1, Item 1A, and Item 7 sections using regex markers."""
        sections = {
            "business": "",
            "risk_factors": "",
            "mda": ""
        }

        # Item 1: Business
        match_item1 = re.search(r"ITEM\s+1\.\s+BUSINESS(.*?)ITEM\s+1A\.", self.raw_text, re.DOTALL | re.IGNORECASE)
        if match_item1:
            sections["business"] = match_item1.group(1).strip()

        # Item 1A: Risk Factors
        match_item1a = re.search(r"ITEM\s+1A\.\s+RISK\s+FACTORS(.*?)ITEM\s+7\.", self.raw_text, re.DOTALL | re.IGNORECASE)
        if not match_item1a:
            match_item1a = re.search(r"ITEM\s+1A\.\s+RISK\s+FACTORS(.*?)(ITEM\s+1B\.|ITEM\s+2\.|ITEM\s+7\.)", self.raw_text, re.DOTALL | re.IGNORECASE)
        
        if match_item1a:
            sections["risk_factors"] = match_item1a.group(1).strip()

        # Item 7: MD&A
        match_item7 = re.search(r"ITEM\s+7\.\s+MANAGEMENT.*?ANALYSIS.*?(.*?)(ITEM\s+7A\.|ITEM\s+8\.|$)", self.raw_text, re.DOTALL | re.IGNORECASE)
        if match_item7:
            sections["mda"] = match_item7.group(1).strip()

        # Fallback if specific tags are missing
        if not any(sections.values()):
            sections["mda"] = self.raw_text[:4000]

        return sections
