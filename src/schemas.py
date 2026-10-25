from typing import List, Optional
from pydantic import BaseModel, Field


class MetricComparison(BaseModel):
    metric_name: str
    current_year_val: Optional[float] = Field(default=None, description="Value in millions USD or absolute EPS; None if not reported")
    prior_year_val: Optional[float] = Field(default=None, description="Value in millions USD or absolute EPS; None if not reported")
    yoy_change_pct: Optional[float] = Field(default=None, description="Percentage change year over year; None if not computable")
    unit: str = Field(default="$M", description="Unit of measurement ($M, $, %)")
    trend: str = Field(default="Not Reported", description="Positive, Negative, Neutral, or Not Reported")

    @property
    def reported(self) -> bool:
        return self.current_year_val is not None and self.prior_year_val is not None

    def _fmt(self, value: Optional[float]) -> str:
        if value is None:
            return "N/A"
        if self.unit == "$M":
            return f"${value}M"
        if self.unit == "%":
            return f"{value}%"
        return f"{self.unit}{value}"

    @property
    def current_display(self) -> str:
        return self._fmt(self.current_year_val)

    @property
    def prior_display(self) -> str:
        return self._fmt(self.prior_year_val)

    @property
    def change_display(self) -> str:
        if self.yoy_change_pct is None:
            return "N/A"
        return f"{'+' if self.yoy_change_pct > 0 else ''}{self.yoy_change_pct}%"

    @property
    def chart_current(self) -> str:
        """JavaScript literal for charts: the number, or null when not reported."""
        return "null" if self.current_year_val is None else str(self.current_year_val)

    @property
    def chart_prior(self) -> str:
        return "null" if self.prior_year_val is None else str(self.prior_year_val)


class FinancialMetrics(BaseModel):
    fiscal_year: int
    prior_fiscal_year: int
    revenue: MetricComparison
    operating_expenses: MetricComparison
    net_income: MetricComparison
    eps: MetricComparison
    operating_cash_flow: MetricComparison


class RiskFactorCard(BaseModel):
    id: str
    title: str
    category: str = Field(..., description="Cybersecurity, AI Disruption, Macroeconomic, Regulatory, Supply Chain, etc.")
    severity: str = Field(..., description="HIGH, MEDIUM, or LOW")
    summary: str = Field(..., description="Concise explanation of the risk impact")
    mitigation_strategy: Optional[str] = Field(default=None, description="Company's response or countermeasure")


class ExecutiveSummary(BaseModel):
    company_name: str
    fiscal_year: int
    overall_health_score: float = Field(..., description="Score out of 10 for financial health & growth outlook")
    sentiment_label: str = Field(..., description="Strong Bullish, Bullish, Neutral, Bearish")
    key_growth_drivers: List[str]
    management_guidance: str


class FinancialAnalysisReport(BaseModel):
    report_title: str
    generated_at: str
    executive_summary: ExecutiveSummary
    metrics: FinancialMetrics
    risk_factors: List[RiskFactorCard]
