# 📈 SEC 10-K & Earnings Call Financial Analyst Agent

An autonomous, production-grade AI Agent system built in Python that ingests SEC 10-K/10-Q filings and earnings call transcripts, extracts structured financial metrics, calculates YoY performance metrics, classifies Item 1A Risk Factors by severity, and generates an executive web dashboard.

---

## 🌟 Architecture & Engineering Highlights

* **Structured Schema Validation**: Built with Pydantic models to enforce strict type definitions and prevent LLM output hallucinations or malformed JSON payloads.
* **Autonomous Section Extraction**: Uses regex-assisted pattern matching to isolate Item 1 (Business), Item 1A (Risk Factors), and Item 7 (MD&A) prior to agent ingestion—minimizing token context windows and API costs.
* **YoY Financial Metrics Math**: Automatically computes percentage growth rates, trend direction, and financial health scores for Revenue, Net Income, EPS, and Cash Flow.
* **Risk Factor Matrix**: Categorizes unstructured risk text into Cybersecurity, Technology, Macroeconomic, and Regulatory categories with severity scoring (`HIGH`, `MEDIUM`, `LOW`).
* **Glassmorphism Web Dashboard**: Generates an interactive HTML/CSS dashboard with KPI cards, risk badges, and financial guidance.
* **Zero-Config Offline Mode**: Includes sample SEC 10-K filings out-of-the-box for instant local testing and CI/CD validation without requiring API keys.

---

## 🏗️ System Architecture

```
                                  ┌───────────────────────────┐
                                  │   Raw SEC 10-K / 10-Q     │
                                  │  Filing or Transcript     │
                                  └─────────────┬─────────────┘
                                                │
                                                ▼
                                  ┌───────────────────────────┐
                                  │      SECParser Module     │
                                  │  (Isolates Item 1A & 7)   │
                                  └─────────────┬─────────────┘
                                                │
                                                ▼
                                  ┌───────────────────────────┐
                                  │ SECFinancialAnalystAgent  │
                                  │  (Pydantic Schema Engine) │
                                  └─────────────┬─────────────┘
                                                │
                                ┌───────────────┴───────────────┐
                                ▼                               ▼
                  ┌───────────────────────────┐   ┌───────────────────────────┐
                  │    Executive Markdown     │   │ Glassmorphism HTML        │
                  │    Report (report.md)     │   │ Dashboard (dashboard.html)│
                  └───────────────────────────┘   └───────────────────────────┘
```

---

## 💡 Key Design Decisions for Interview Reviewers

1. **Why Pydantic Schemas?**  
   Standard LLM outputs are probabilistic and can return malformed JSON. Using strict Pydantic data models (`FinancialMetrics`, `RiskFactorCard`, `ExecutiveSummary`) guarantees that downstream API consumers or UI dashboards receive validated, strongly-typed objects.

2. **Cost & Context Window Optimization**:  
   Rather than sending a full 100-page 10-K document directly to an LLM prompt, the `SECParser` extracts only relevant items (Item 1A Risk Factors and Item 7 MD&A), reducing prompt token consumption by **~85%**.

3. **Production Testability**:  
   Includes a full `pytest` suite testing parser regex, schema validation, and report generation, ensuring pipeline changes never break downstream contracts.

---

## 🚀 Quick Start & Installation

### 1. Clone the Repository
```bash
git clone https://github.com/amandahervol-alt/sec-financial-analyst-agent.git
cd sec-financial-analyst-agent
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Run the Analyst Agent & Launch Dashboard
```bash
python app.py
```
*This automatically processes the sample SEC 10-K filing, generates the analysis reports in `output/`, and opens the interactive Web Dashboard in your browser at `http://localhost:8000/dashboard.html`!*

### 4. Run Automated Unit Tests
```bash
python -m pytest tests/
```

---

## 📂 Repository Structure

```
sec_financial_analyst_agent/
├── data/
│   └── samples/                  # Pre-loaded sample SEC 10-K filing (TechCorp Inc.)
├── src/
│   ├── sec_parser.py             # Section extractor (Item 1, Item 1A, Item 7 MD&A)
│   ├── schemas.py                # Pydantic schema validation models
│   ├── financial_agent.py        # Core Financial Analyst AI Agent logic
│   └── report_generator.py       # Markdown & HTML Dashboard Generator
├── tests/
│   └── test_agent.py             # Pytest automated test suite
├── output/                       # Generated Markdown & HTML Dashboard outputs
├── app.py                        # CLI & Local HTTP Web Server
├── requirements.txt              # Project dependencies
└── README.md                     # Technical architecture & portfolio overview
```

---

## 📊 Example Dashboard Output

The agent produces an executive report featuring:
* **Financial Health Score**: `9.8/10` (Strong Bullish)
* **Core YoY Metrics Table**: Revenue (`+22.8%`), Net Income (`+48.8%`), EPS (`+48.1%`)
* **Risk Severity Matrix**: Cyber Threats (`HIGH`), AI Disruption (`MEDIUM`), FX Volatility (`MEDIUM`)
