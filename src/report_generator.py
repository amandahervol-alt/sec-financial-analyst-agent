import os
from jinja2 import Template
from src.schemas import FinancialAnalysisReport


class ReportGenerator:
    """Generates Markdown and interactive glassmorphism HTML dashboards from FinancialAnalysisReport objects."""

    def __init__(self, report: FinancialAnalysisReport):
        self.report = report

    def generate_markdown(self) -> str:
        r = self.report
        m = r.metrics
        e = r.executive_summary

        md = f"""# 📈 {r.report_title}
**Generated**: {r.generated_at}

## 📊 Executive Summary
* **Company**: {e.company_name} (FY{e.fiscal_year})
* **Financial Health Score**: `{e.overall_health_score}/10`
* **Overall Sentiment**: **{e.sentiment_label}**
* **Management Guidance**: {e.management_guidance}

### Key Growth Drivers
"""
        for driver in e.key_growth_drivers:
            md += f"- {driver}\n"

        md += f"""
---

## 💵 Core Financial Metrics (YoY Comparison)

| Metric | FY{m.prior_fiscal_year} | FY{m.fiscal_year} | YoY Change (%) | Trend |
| :--- | :--- | :--- | :--- | :--- |
| **Revenue** | ${m.revenue.prior_year_val}M | ${m.revenue.current_year_val}M | `+{m.revenue.yoy_change_pct}%` | {m.revenue.trend} |
| **Operating Expenses** | ${m.operating_expenses.prior_year_val}M | ${m.operating_expenses.current_year_val}M | `+{m.operating_expenses.yoy_change_pct}%` | {m.operating_expenses.trend} |
| **Net Income** | ${m.net_income.prior_year_val}M | ${m.net_income.current_year_val}M | `+{m.net_income.yoy_change_pct}%` | {m.net_income.trend} |
| **Diluted EPS** | ${m.eps.prior_year_val} | ${m.eps.current_year_val} | `+{m.eps.yoy_change_pct}%` | {m.eps.trend} |
| **Operating Cash Flow** | ${m.operating_cash_flow.prior_year_val}M | ${m.operating_cash_flow.current_year_val}M | `+{m.operating_cash_flow.yoy_change_pct}%` | {m.operating_cash_flow.trend} |

---

## ⚠️ Risk Factor Matrix (Item 1A Analysis)

"""
        for card in r.risk_factors:
            md += f"""### [{card.id}] {card.title}
* **Category**: `{card.category}` | **Severity**: **{card.severity}**
* **Impact**: {card.summary}
* **Mitigation**: {card.mitigation_strategy or 'N/A'}

"""
        return md

    def generate_html(self) -> str:
        """Generate sleek, responsive glassmorphism HTML dashboard."""
        r = self.report
        m = r.metrics
        e = r.executive_summary

        html_template = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ r.report_title }}</title>
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;700&family=Inter:wght@400;500;600&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg: #0b0f19;
            --card-bg: rgba(22, 30, 49, 0.7);
            --border: rgba(255, 255, 255, 0.08);
            --accent-blue: #38bdf8;
            --accent-green: #4ade80;
            --accent-red: #f87171;
            --accent-purple: #c084fc;
            --text-main: #f3f4f6;
            --text-muted: #9ca3af;
        }

        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            font-family: 'Inter', sans-serif;
            background: var(--bg);
            color: var(--text-main);
            padding: 2rem;
            line-height: 1.6;
            background-image: 
                radial-gradient(circle at 15% 20%, rgba(56, 189, 248, 0.12) 0%, transparent 40%),
                radial-gradient(circle at 85% 75%, rgba(192, 132, 252, 0.12) 0%, transparent 40%);
            min-height: 100vh;
        }

        .container { max-width: 1200px; margin: 0 auto; }

        header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 2rem;
            padding-bottom: 1.5rem;
            border-bottom: 1px solid var(--border);
        }

        h1 { font-family: 'Outfit', sans-serif; font-size: 2rem; font-weight: 700; color: #fff; }
        .timestamp { color: var(--text-muted); font-size: 0.9rem; }

        .dashboard-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 1.5rem;
            margin-bottom: 2.5rem;
        }

        .card {
            background: var(--card-bg);
            backdrop-filter: blur(12px);
            border: 1px solid var(--border);
            border-radius: 16px;
            padding: 1.5rem;
            box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
        }

        .metric-title { font-size: 0.85rem; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.05em; font-weight: 600; }
        .metric-val { font-family: 'Outfit', sans-serif; font-size: 2.2rem; font-weight: 700; margin: 0.4rem 0; }
        .metric-change { font-size: 0.9rem; font-weight: 600; display: inline-flex; align-items: center; gap: 0.3rem; padding: 0.25rem 0.6rem; border-radius: 20px; }
        .badge-positive { background: rgba(74, 222, 128, 0.15); color: var(--accent-green); }
        .badge-negative { background: rgba(248, 113, 113, 0.15); color: var(--accent-red); }

        .section-title {
            font-family: 'Outfit', sans-serif;
            font-size: 1.4rem;
            margin-bottom: 1.2rem;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }

        table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 1rem;
        }

        th, td {
            padding: 1rem;
            text-align: left;
            border-bottom: 1px solid var(--border);
        }

        th { color: var(--text-muted); font-size: 0.85rem; text-transform: uppercase; letter-spacing: 0.05em; }

        .risk-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(340px, 1fr));
            gap: 1.5rem;
        }

        .risk-card {
            background: var(--card-bg);
            border: 1px solid var(--border);
            border-left: 4px solid var(--accent-blue);
            border-radius: 12px;
            padding: 1.25rem;
        }

        .risk-card.severity-HIGH { border-left-color: var(--accent-red); }
        .risk-card.severity-MEDIUM { border-left-color: #fbbf24; }

        .severity-tag {
            font-size: 0.75rem;
            font-weight: 700;
            padding: 0.2rem 0.5rem;
            border-radius: 4px;
            text-transform: uppercase;
        }
        .severity-HIGH .severity-tag { background: rgba(248, 113, 113, 0.2); color: var(--accent-red); }
        .severity-MEDIUM .severity-tag { background: rgba(251, 191, 36, 0.2); color: #fbbf24; }

        .bullet-list { margin-left: 1.2rem; margin-top: 0.5rem; }
        .bullet-list li { margin-bottom: 0.4rem; color: #e5e7eb; }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <div>
                <h1>{{ r.report_title }}</h1>
                <div class="timestamp">Generated by Autonomous SEC Financial Analyst Agent • {{ r.generated_at }}</div>
            </div>
            <div style="text-align: right;">
                <span style="font-size: 0.85rem; color: var(--text-muted);">Health Score</span>
                <div style="font-family: 'Outfit'; font-size: 2rem; font-weight: 700; color: var(--accent-blue);">{{ e.overall_health_score }}/10</div>
            </div>
        </header>

        <!-- KPI Grid -->
        <div class="dashboard-grid">
            <div class="card">
                <div class="metric-title">Total Revenue</div>
                <div class="metric-val">${{ m.revenue.current_year_val }}M</div>
                <div class="metric-change badge-positive">▲ +{{ m.revenue.yoy_change_pct }}% YoY</div>
            </div>
            <div class="card">
                <div class="metric-title">Net Income</div>
                <div class="metric-val">${{ m.net_income.current_year_val }}M</div>
                <div class="metric-change badge-positive">▲ +{{ m.net_income.yoy_change_pct }}% YoY</div>
            </div>
            <div class="card">
                <div class="metric-title">Diluted EPS</div>
                <div class="metric-val">${{ m.eps.current_year_val }}</div>
                <div class="metric-change badge-positive">▲ +{{ m.eps.yoy_change_pct }}% YoY</div>
            </div>
            <div class="card">
                <div class="metric-title">Operating Cash Flow</div>
                <div class="metric-val">${{ m.operating_cash_flow.current_year_val }}M</div>
                <div class="metric-change badge-positive">▲ +{{ m.operating_cash_flow.yoy_change_pct }}% YoY</div>
            </div>
        </div>

        <!-- Executive Summary -->
        <div class="card" style="margin-bottom: 2.5rem;">
            <div class="section-title">💡 Executive Summary & Growth Guidance</div>
            <p><strong>Sentiment:</strong> <span style="color: var(--accent-green); font-weight: 600;">{{ e.sentiment_label }}</span></p>
            <p style="margin-top: 0.5rem;"><strong>Management Guidance:</strong> {{ e.management_guidance }}</p>
            <div style="margin-top: 1rem;">
                <strong>Key Growth Drivers:</strong>
                <ul class="bullet-list">
                    {% for driver in e.key_growth_drivers %}
                    <li>{{ driver }}</li>
                    {% endfor %}
                </ul>
            </div>
        </div>

        <!-- Risk Factors -->
        <div class="section-title">⚠️ Item 1A Risk Factor Classification</div>
        <div class="risk-grid">
            {% for risk in r.risk_factors %}
            <div class="risk-card severity-{{ risk.severity }}">
                <div style="display: flex; justify-space-between; align-items: center; margin-bottom: 0.5rem;">
                    <span style="font-weight: 600; color: #fff;">{{ risk.title }}</span>
                    <span class="severity-tag">{{ risk.severity }}</span>
                </div>
                <p style="font-size: 0.9rem; color: var(--text-muted); margin-bottom: 0.5rem;"><strong>Category:</strong> {{ risk.category }}</p>
                <p style="font-size: 0.9rem;">{{ risk.summary }}</p>
            </div>
            {% endfor %}
        </div>
    </div>
</body>
</html>
"""
        template = Template(html_template)
        return template.render(r=r, m=m, e=e)
