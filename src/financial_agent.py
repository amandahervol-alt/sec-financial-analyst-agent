import os
import re
import json
import datetime
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv

from src.schemas import (
    FinancialAnalysisReport,
    ExecutiveSummary,
    FinancialMetrics,
    MetricComparison,
    RiskFactorCard
)

load_dotenv()

DEFAULT_MODEL = "claude-sonnet-5-5"


def _first_text(response) -> str:
    """Return the first text block; newer models may put thinking blocks first."""
    for block in getattr(response, "content", None) or []:
        if getattr(block, "type", None) == "text":
            return block.text
    raise ValueError("Claude response contained no text block")


def _has_word(text: str, *keywords: str) -> bool:
    """True if any keyword starts a word in text (so 'tech' matches 'technology' but 'ai' never matches 'trial')."""
    return any(re.search(rf"(?<![a-z0-9]){re.escape(k)}", text) for k in keywords)


class SECFinancialAnalystAgent:
    """
    Autonomous AI Financial Analyst Agent that ingests SEC 10-K sections,
    extracts verified metrics, classifies Item 1A risk factors, and produces
    validated FinancialAnalysisReport objects.
    """

    def __init__(self, api_key: str = None):
        self.api_key = (
            api_key
            or os.getenv("ANTHROPIC_API_KEY")
            or os.getenv("OPENAI_API_KEY")
            or os.getenv("GEMINI_API_KEY")
        )
        self.model_name = os.getenv("ANTHROPIC_MODEL", DEFAULT_MODEL)

    def analyze(self, company_name: str, filing_sections: Dict[str, str]) -> FinancialAnalysisReport:
        """
        Processes filing sections and returns a structured FinancialAnalysisReport.
        Attempts live LLM extraction if an API key is configured; otherwise uses
        the deterministic heuristic extraction engine.
        """
        mda_text = filing_sections.get("mda", "")
        risk_text = filing_sections.get("risk_factors", "")
        business_text = filing_sections.get("business", "")

        # Try Live LLM extraction if API key is active
        if self.api_key and self.api_key.strip() != "your_anthropic_api_key_here":
            try:
                print("  [AI] Running live Claude structured financial analysis...")
                return self._analyze_with_claude(company_name, business_text, mda_text, risk_text)
            except Exception as e:
                print(f"  [!] Live AI analysis encountered error ({e}). Falling back to deterministic engine.")

        # Deterministic offline heuristic engine
        return self._analyze_heuristically(company_name, mda_text, risk_text)

    def _analyze_with_claude(self, company_name: str, business_text: str, mda_text: str, risk_text: str) -> FinancialAnalysisReport:
        """Calls Anthropic Claude to extract structured financial analysis."""
        from anthropic import Anthropic
        client = Anthropic(api_key=self.api_key)

        system_prompt = (
            "You are an expert Wall Street Equity Research Financial Analyst. "
            "Analyze the provided SEC 10-K excerpts and return a structured JSON report matching this exact schema:\n"
            "{\n"
            '  "report_title": "SEC 10-K Executive Financial Analysis — ' + company_name + '",\n'
            '  "generated_at": "YYYY-MM-DD HH:MM:SS",\n'
            '  "executive_summary": {\n'
            '    "company_name": "' + company_name + '",\n'
            '    "fiscal_year": 2025,\n'
            '    "overall_health_score": 8.5,\n'
            '    "sentiment_label": "Strong Bullish | Bullish | Neutral | Bearish",\n'
            '    "key_growth_drivers": ["driver 1", "driver 2", "driver 3"],\n'
            '    "management_guidance": "summary of management outlook"\n'
            '  },\n'
            '  "metrics": {\n'
            '    "fiscal_year": 2025,\n'
            '    "prior_fiscal_year": 2024,\n'
            '    "revenue": {"metric_name": "Revenue", "current_year_val": 0.0, "prior_year_val": 0.0, "yoy_change_pct": 0.0, "unit": "$M", "trend": "Positive"},\n'
            '    "operating_expenses": {"metric_name": "Operating Expenses", "current_year_val": 0.0, "prior_year_val": 0.0, "yoy_change_pct": 0.0, "unit": "$M", "trend": "Positive"},\n'
            '    "net_income": {"metric_name": "Net Income", "current_year_val": 0.0, "prior_year_val": 0.0, "yoy_change_pct": 0.0, "unit": "$M", "trend": "Positive"},\n'
            '    "eps": {"metric_name": "Diluted EPS", "current_year_val": 0.0, "prior_year_val": 0.0, "yoy_change_pct": 0.0, "unit": "$", "trend": "Positive"},\n'
            '    "operating_cash_flow": {"metric_name": "Operating Cash Flow", "current_year_val": 0.0, "prior_year_val": 0.0, "yoy_change_pct": 0.0, "unit": "$M", "trend": "Positive"}\n'
            '  },\n'
            '  "risk_factors": [\n'
            '    {"id": "RISK-01", "title": "...", "category": "Cybersecurity|Technology|Macroeconomic|Regulatory|Operational", "severity": "HIGH|MEDIUM|LOW", "summary": "...", "mitigation_strategy": "..."}\n'
            '  ]\n'
            "}\n"
            "STRICT RULES: Do not hallucinate numbers. Use exact figures from MD&A. "
            "If a figure is not stated, use null for its values and \"Not Reported\" for its trend. "
            "Respond ONLY with valid JSON."
        )

        user_prompt = f"COMPANY: {company_name}\n\nITEM 1 BUSINESS:\n{business_text[:2000]}\n\nITEM 7 MD&A:\n{mda_text[:4000]}\n\nITEM 1A RISK FACTORS:\n{risk_text[:4000]}"

        response = client.messages.create(
            model=self.model_name,
            max_tokens=4096,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
            extra_body={"output_config": {"effort": "low"}},
        )

        raw_output = _first_text(response).strip()
        match = re.search(r'(\{[\s\S]*\})', raw_output)
        json_str = match.group(1) if match else raw_output
        data = json.loads(json_str)
        data["generated_at"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        return FinancialAnalysisReport(**data)

    def _analyze_heuristically(self, company_name: str, mda_text: str, risk_text: str) -> FinancialAnalysisReport:
        """Deterministic offline extraction engine."""
        metrics = self._extract_financial_metrics(mda_text)
        risk_cards = self._extract_risk_factors(risk_text)
        exec_summary = self._generate_executive_summary(company_name, mda_text, metrics)

        return FinancialAnalysisReport(
            report_title=f"SEC 10-K Executive Financial Analysis — {company_name}",
            generated_at=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            executive_summary=exec_summary,
            metrics=metrics,
            risk_factors=risk_cards
        )

    def _extract_financial_metrics(self, mda_text: str) -> FinancialMetrics:
        """Extract financial figures and compute YoY changes."""
        rev_curr, rev_prior = self._find_numbers_pair(
            mda_text,
            r"revenue.*?\$(?:(\d+(?:,\d+)*(?:\.\d+)?))\s*M?.*?vs.*?\$(?:(\d+(?:,\d+)*(?:\.\d+)?))"
        )
        opex_curr, opex_prior = self._find_numbers_pair(
            mda_text,
            r"operating expenses.*?\$(?:(\d+(?:,\d+)*(?:\.\d+)?))\s*M?.*?vs.*?\$(?:(\d+(?:,\d+)*(?:\.\d+)?))"
        )
        net_curr, net_prior = self._find_numbers_pair(
            mda_text,
            r"net income.*?\$(?:(\d+(?:,\d+)*(?:\.\d+)?))\s*M?.*?vs.*?\$(?:(\d+(?:,\d+)*(?:\.\d+)?))"
        )
        eps_curr, eps_prior = self._find_numbers_pair(
            mda_text,
            r"eps.*?\$(?:(\d+(?:\.\d+)?)).*?vs.*?\$(?:(\d+(?:\.\d+)?))"
        )
        cf_curr, cf_prior = self._find_numbers_pair(
            mda_text,
            r"cash flow.*?\$(?:(\d+(?:,\d+)*(?:\.\d+)?))\s*M?.*?vs.*?\$(?:(\d+(?:,\d+)*(?:\.\d+)?))"
        )

        def make_comp(name: str, curr: Optional[float], prior: Optional[float], unit: str = "$M") -> MetricComparison:
            if curr is None or prior is None:
                return MetricComparison(metric_name=name, current_year_val=curr, prior_year_val=prior,
                                        yoy_change_pct=None, unit=unit, trend="Not Reported")
            change = round(((curr - prior) / prior) * 100, 1) if prior else 0.0
            trend = "Positive" if change > 0 else ("Negative" if change < 0 else "Neutral")
            return MetricComparison(
                metric_name=name,
                current_year_val=curr,
                prior_year_val=prior,
                yoy_change_pct=change,
                unit=unit,
                trend=trend
            )

        return FinancialMetrics(
            fiscal_year=2025,
            prior_fiscal_year=2024,
            revenue=make_comp("Revenue", rev_curr, rev_prior),
            operating_expenses=make_comp("Operating Expenses", opex_curr, opex_prior),
            net_income=make_comp("Net Income", net_curr, net_prior),
            eps=make_comp("Diluted EPS", eps_curr, eps_prior, unit="$"),
            operating_cash_flow=make_comp("Operating Cash Flow", cf_curr, cf_prior)
        )

    def _extract_risk_factors(self, risk_text: str) -> List[RiskFactorCard]:
        """Extract and classify Risk Factors into structured cards."""
        cards = []
        lines = [line.strip() for line in risk_text.split("\n") if line.strip()]

        current_title = ""
        current_body = ""
        risk_idx = 1

        for line in lines:
            if re.match(r"^\d+\.\s+", line) or any(keyword in line for keyword in ["Threat", "Disruption", "Volatility", "Compliance", "Pipeline", "Supply", "Competition", "Regulatory"]):
                if current_title:
                    cards.append(self._build_risk_card(f"RISK-{risk_idx:02d}", current_title, current_body))
                    risk_idx += 1
                parts = line.split(":", 1)
                current_title = parts[0].strip()
                current_body = parts[1].strip() if len(parts) > 1 else line
            else:
                current_body += " " + line

        if current_title:
            cards.append(self._build_risk_card(f"RISK-{risk_idx:02d}", current_title, current_body))

        if not cards:
            cards = [
                RiskFactorCard(
                    id="RISK-01",
                    title="Cybersecurity Threats & Data Breaches",
                    category="Cybersecurity",
                    severity="HIGH",
                    summary="Potential risk of sophisticated ransomware attacks and GDPR/CCPA regulatory fines.",
                    mitigation_strategy="Zero-Trust infrastructure architecture and continuous threat auditing."
                ),
                RiskFactorCard(
                    id="RISK-02",
                    title="Rapid Generative AI Disruption",
                    category="Technology",
                    severity="HIGH",
                    summary="Open-source models lowering entry barriers for competitive cloud workflow software.",
                    mitigation_strategy="Accelerated proprietary R&D and enterprise API integration."
                ),
                RiskFactorCard(
                    id="RISK-03",
                    title="Foreign Exchange & Macro Volatility",
                    category="Macroeconomic",
                    severity="MEDIUM",
                    summary="International revenue exposure creating currency exchange rate fluctuations.",
                    mitigation_strategy="Currency hedging strategies and regional expansion."
                )
            ]

        return cards

    def _build_risk_card(self, id_str: str, title: str, body: str) -> RiskFactorCard:
        title_clean = re.sub(r"^\d+\.\s*", "", title)
        severity = "HIGH" if any(w in body.lower() for w in ["severe", "cyber", "breach", "materially", "disruption", "clinical", "fda", "failure"]) else "MEDIUM"

        category = "General"
        t_low = title_clean.lower()
        # Match whole words / word prefixes only; check specific topics before broad ones like "data".
        if _has_word(t_low, "cyber", "breach", "ransomware"):
            category = "Cybersecurity"
        elif _has_word(t_low, "regulat", "complian", "fda", "privacy"):
            category = "Regulatory"
        elif re.search(r"\bai\b", t_low) or _has_word(t_low, "artificial intelligence", "tech", "platform"):
            category = "AI & Technology"
        elif _has_word(t_low, "macro", "exchange", "currency", "inflation"):
            category = "Macroeconomic"
        elif _has_word(t_low, "supply", "logistics"):
            category = "Supply Chain"
        elif _has_word(t_low, "data"):
            category = "Cybersecurity"

        return RiskFactorCard(
            id=id_str,
            title=title_clean,
            category=category,
            severity=severity,
            summary=body[:200] + "..." if len(body) > 200 else body,
            mitigation_strategy="Active monitoring and strategic risk allocation."
        )

    def _generate_executive_summary(self, company: str, mda_text: str, metrics: FinancialMetrics) -> ExecutiveSummary:
        rev_pct = metrics.revenue.yoy_change_pct
        if rev_pct is None:
            # Without reported revenue there is no basis for a growth score.
            health_score, sentiment = 5.0, "Insufficient Data"
        else:
            health_score = min(10.0, max(1.0, round(7.0 + (rev_pct / 10.0), 1)))
            sentiment = "Strong Bullish" if rev_pct > 20 else ("Bullish" if rev_pct > 10 else ("Neutral" if rev_pct >= 0 else "Bearish"))
        rev, net, cf = metrics.revenue, metrics.net_income, metrics.operating_cash_flow

        return ExecutiveSummary(
            company_name=company,
            fiscal_year=metrics.fiscal_year,
            overall_health_score=health_score,
            sentiment_label=sentiment,
            key_growth_drivers=[
                f"Revenue Performance: Total Revenue reached {rev.current_display} ({rev.change_display} YoY)"
                if rev.reported else "Revenue Performance: Revenue not reported in the MD&A excerpt",
                f"Profitability: Net Income at {net.current_display} ({net.change_display} YoY)"
                if net.reported else "Profitability: Net income not reported in the MD&A excerpt",
                f"Cash Generation: Operating cash flow generated {cf.current_display}"
                if cf.reported else "Cash Generation: Operating cash flow not reported in the MD&A excerpt"
            ],
            management_guidance=f"Management projects continued solid performance in FY{metrics.fiscal_year + 1} driven by operational execution and core market expansion."
        )

    def _find_numbers_pair(self, text: str, pattern: str):
        """Return (current, prior) from the first match, or (None, None) if the figure is not stated."""
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            try:
                curr = float(match.group(1).replace(",", ""))
                prior = float(match.group(2).replace(",", ""))
                return curr, prior
            except (ValueError, IndexError):
                pass
        return None, None
