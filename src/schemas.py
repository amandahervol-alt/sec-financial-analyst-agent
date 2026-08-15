from typing import List, Optional
from pydantic import BaseModel, Field


class MetricComparison(BaseModel):
    metric_name: str
    current_year_val: float = Field(..., description="Value in millions USD or absolute EPS")
    prior_year_val: float = Field(..., description="Value in millions USD or absolute EPS")
    yoy_change_pct: float = Field(..., description="Percentage change year over year")
    unit: str = Field(default="$M", description="Unit of measurement ($M, $, %)")
    trend: str = Field(..., description="Positive, Negative, or Neutral")


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
