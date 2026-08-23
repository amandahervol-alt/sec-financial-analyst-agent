# SEC Financial Analyst Agent — AI Orchestration Guide
AGENTS.md — Antigravity Orchestration Architecture

This system operates as an autonomous financial analyst AI agent that digests raw corporate SEC 10-K/10-Q filings, extracts verified metrics, classifies Item 1A risk factors, and produces executive-ready dashboards.

## The 3-Layer Architecture

### Layer 1: Ingestion & Parsing (`src/sec_parser.py`)
- Isolates critical filing sections: **Item 1** (Business Overview), **Item 1A** (Risk Factors), and **Item 7** (Management's Discussion & Analysis).
- Strips irrelevant legal boilerplate, reducing context window consumption by **~85%**.

### Layer 2: AI Reasoning & Schema Validation (`src/financial_agent.py` & `src/schemas.py`)
- Extracts structured financial metrics into Pydantic models (`FinancialMetrics`, `MetricComparison`, `RiskFactorCard`, `ExecutiveSummary`).
- Calculates deterministic YoY percentage changes and health scores.
- Supports **Dual-Mode Execution**:
  - **Live AI Mode**: Uses Anthropic Claude / Gemini API for deep natural language extraction and nuance detection.
  - **Offline Heuristic Mode**: Uses deterministic regex pattern matching for instant local testing and CI/CD without API keys.

### Layer 3: Presentation & Reporting (`src/report_generator.py`)
- Renders dual deliverables:
  - `output/report.md` — Copy-paste ready GitHub-flavored Markdown executive summary.
  - `output/dashboard.html` — Interactive glassmorphism HTML web dashboard featuring Chart.js visual financial trends.

## Operating Principles
1. **Never Hallucinate Financials**: Financial figures must be grounded in raw filing numbers or calculated via deterministic math.
2. **Strict Schema Contracts**: All agent outputs must validate against Pydantic models before rendering.
3. **Graceful Fallbacks**: If no LLM API key is present in `.env`, the system automatically activates the offline deterministic parser.
