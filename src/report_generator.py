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
| **Revenue** | {m.revenue.prior_display} | {m.revenue.current_display} | `{m.revenue.change_display}` | {m.revenue.trend} |
| **Operating Expenses** | {m.operating_expenses.prior_display} | {m.operating_expenses.current_display} | `{m.operating_expenses.change_display}` | {m.operating_expenses.trend} |
| **Net Income** | {m.net_income.prior_display} | {m.net_income.current_display} | `{m.net_income.change_display}` | {m.net_income.trend} |
| **Diluted EPS** | {m.eps.prior_display} | {m.eps.current_display} | `{m.eps.change_display}` | {m.eps.trend} |
| **Operating Cash Flow** | {m.operating_cash_flow.prior_display} | {m.operating_cash_flow.current_display} | `{m.operating_cash_flow.change_display}` | {m.operating_cash_flow.trend} |

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
        """Generate sleek, responsive glassmorphism HTML dashboard with Chart.js analytics."""
        r = self.report
        m = r.metrics
        e = r.executive_summary

        # Calculate severity counts for donut chart
        high_count = sum(1 for c in r.risk_factors if c.severity == "HIGH")
        med_count = sum(1 for c in r.risk_factors if c.severity == "MEDIUM")
        low_count = sum(1 for c in r.risk_factors if c.severity == "LOW")

        html_template = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ r.report_title }}</title>
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;700;800&family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        :root {
            --bg: #070a13;
            --card-bg: rgba(18, 24, 40, 0.75);
            --card-border: rgba(255, 255, 255, 0.08);
            --accent-cyan: #06b6d4;
            --accent-blue: #38bdf8;
            --accent-green: #10b981;
            --accent-purple: #a855f7;
            --accent-red: #ef4444;
            --accent-yellow: #f59e0b;
            --text-main: #f8fafc;
            --text-muted: #94a3b8;
            --text-dim: #64748b;
        }

        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            font-family: 'Inter', system-ui, sans-serif;
            background: var(--bg);
            color: var(--text-main);
            padding: 2.5rem 1.5rem;
            line-height: 1.6;
            background-image: 
                radial-gradient(circle at 10% 15%, rgba(6, 182, 212, 0.12) 0%, transparent 40%),
                radial-gradient(circle at 90% 85%, rgba(168, 85, 247, 0.12) 0%, transparent 40%),
                radial-gradient(circle at 50% 50%, rgba(16, 185, 129, 0.05) 0%, transparent 50%);
            background-attachment: fixed;
            min-height: 100vh;
        }

        .container { max-width: 1320px; margin: 0 auto; }

        header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 2.5rem;
            padding-bottom: 1.75rem;
            border-bottom: 1px solid var(--card-border);
            flex-wrap: wrap;
            gap: 1.5rem;
        }

        .brand-title {
            font-family: 'Outfit', sans-serif;
            font-size: 2.2rem;
            font-weight: 800;
            letter-spacing: -0.02em;
            background: linear-gradient(135deg, #38bdf8 0%, #a855f7 50%, #10b981 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            display: inline-block;
        }

        .timestamp { color: var(--text-muted); font-size: 0.85rem; margin-top: 0.25rem; }

        .health-badge-container {
            text-align: right;
            background: rgba(18, 24, 40, 0.6);
            border: 1px solid var(--card-border);
            padding: 0.75rem 1.25rem;
            border-radius: 12px;
            backdrop-filter: blur(8px);
        }

        .health-score {
            font-family: 'Outfit', sans-serif;
            font-size: 2.2rem;
            font-weight: 800;
            color: var(--accent-cyan);
            line-height: 1.1;
        }

        /* KPI Grid */
        .dashboard-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
            gap: 1.5rem;
            margin-bottom: 2rem;
        }

        .card {
            background: var(--card-bg);
            backdrop-filter: blur(16px);
            border: 1px solid var(--card-border);
            border-radius: 16px;
            padding: 1.5rem;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
            transition: transform 0.2s ease, border-color 0.2s ease;
        }

        .card:hover {
            border-color: rgba(255, 255, 255, 0.15);
        }

        .metric-title { font-size: 0.8rem; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.05em; font-weight: 600; }
        .metric-val { font-family: 'Outfit', sans-serif; font-size: 2.25rem; font-weight: 700; margin: 0.4rem 0; color: #fff; }
        .metric-change { font-size: 0.85rem; font-weight: 600; display: inline-flex; align-items: center; gap: 0.3rem; padding: 0.2rem 0.6rem; border-radius: 20px; }
        .badge-positive { background: rgba(16, 185, 129, 0.15); color: var(--accent-green); border: 1px solid rgba(16, 185, 129, 0.3); }
        .badge-neutral { background: rgba(148, 163, 184, 0.15); color: #94a3b8; border: 1px solid rgba(148, 163, 184, 0.3); }
        .badge-negative { background: rgba(239, 68, 68, 0.15); color: var(--accent-red); border: 1px solid rgba(239, 68, 68, 0.3); }

        /* Chart Section */
        .charts-row {
            display: grid;
            grid-template-columns: 2fr 1fr;
            gap: 1.5rem;
            margin-bottom: 2rem;
        }

        @media (max-width: 992px) {
            .charts-row { grid-template-columns: 1fr; }
        }

        .section-title {
            font-family: 'Outfit', sans-serif;
            font-size: 1.3rem;
            font-weight: 700;
            margin-bottom: 1.2rem;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }

        .chart-container {
            position: relative;
            height: 280px;
            width: 100%;
        }

        /* Executive Summary */
        .exec-card {
            margin-bottom: 2rem;
            background: linear-gradient(180deg, rgba(24, 33, 54, 0.8) 0%, rgba(18, 24, 40, 0.8) 100%);
            border-color: rgba(56, 189, 248, 0.25);
        }

        .bullet-list { margin-left: 1.25rem; margin-top: 0.75rem; }
        .bullet-list li { margin-bottom: 0.45rem; color: #e2e8f0; font-size: 0.95rem; }

        /* Risk Grid */
        .risk-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(360px, 1fr));
            gap: 1.5rem;
        }

        .risk-card {
            background: var(--card-bg);
            border: 1px solid var(--card-border);
            border-left: 4px solid var(--accent-blue);
            border-radius: 12px;
            padding: 1.35rem;
        }

        .risk-card.severity-HIGH { border-left-color: var(--accent-red); }
        .risk-card.severity-MEDIUM { border-left-color: var(--accent-yellow); }
        .risk-card.severity-LOW { border-left-color: var(--accent-green); }

        .risk-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 0.6rem;
        }

        .severity-tag {
            font-size: 0.72rem;
            font-weight: 700;
            padding: 0.2rem 0.55rem;
            border-radius: 4px;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }
        .severity-HIGH .severity-tag { background: rgba(239, 68, 68, 0.2); color: var(--accent-red); border: 1px solid rgba(239, 68, 68, 0.3); }
        .severity-MEDIUM .severity-tag { background: rgba(245, 158, 11, 0.2); color: var(--accent-yellow); border: 1px solid rgba(245, 158, 11, 0.3); }
        .severity-LOW .severity-tag { background: rgba(16, 185, 129, 0.2); color: var(--accent-green); border: 1px solid rgba(16, 185, 129, 0.3); }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <div>
                <h1 class="brand-title">{{ r.report_title }}</h1>
                <div class="timestamp">Autonomous SEC Financial Analyst Agent • FY{{ e.fiscal_year }} 10-K Audit • Generated {{ r.generated_at }}</div>
            </div>
            <div class="health-badge-container">
                <span style="font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.05em; color: var(--text-muted); font-weight: 600;">Financial Health Score</span>
                <div class="health-score">{{ e.overall_health_score }}<span style="font-size: 1.1rem; color: var(--text-dim);">/10</span></div>
            </div>
        </header>

        <!-- KPI Grid -->
        <div class="dashboard-grid">
            <div class="card">
                <div class="metric-title">Total Revenue</div>
                <div class="metric-val">{{ m.revenue.current_display }}</div>
                <div class="metric-change {% if m.revenue.yoy_change_pct is none %}badge-neutral{% elif m.revenue.yoy_change_pct >= 0 %}badge-positive{% else %}badge-negative{% endif %}">
                    {% if m.revenue.yoy_change_pct is none %}Not reported{% else %}{% if m.revenue.yoy_change_pct >= 0 %}▲ {% else %}▼ {% endif %}{{ m.revenue.change_display }} YoY{% endif %}
                </div>
            </div>
            <div class="card">
                <div class="metric-title">Net Income</div>
                <div class="metric-val">{{ m.net_income.current_display }}</div>
                <div class="metric-change {% if m.net_income.yoy_change_pct is none %}badge-neutral{% elif m.net_income.yoy_change_pct >= 0 %}badge-positive{% else %}badge-negative{% endif %}">
                    {% if m.net_income.yoy_change_pct is none %}Not reported{% else %}{% if m.net_income.yoy_change_pct >= 0 %}▲ {% else %}▼ {% endif %}{{ m.net_income.change_display }} YoY{% endif %}
                </div>
            </div>
            <div class="card">
                <div class="metric-title">Diluted EPS</div>
                <div class="metric-val">{{ m.eps.current_display }}</div>
                <div class="metric-change {% if m.eps.yoy_change_pct is none %}badge-neutral{% elif m.eps.yoy_change_pct >= 0 %}badge-positive{% else %}badge-negative{% endif %}">
                    {% if m.eps.yoy_change_pct is none %}Not reported{% else %}{% if m.eps.yoy_change_pct >= 0 %}▲ {% else %}▼ {% endif %}{{ m.eps.change_display }} YoY{% endif %}
                </div>
            </div>
            <div class="card">
                <div class="metric-title">Operating Cash Flow</div>
                <div class="metric-val">{{ m.operating_cash_flow.current_display }}</div>
                <div class="metric-change {% if m.operating_cash_flow.yoy_change_pct is none %}badge-neutral{% elif m.operating_cash_flow.yoy_change_pct >= 0 %}badge-positive{% else %}badge-negative{% endif %}">
                    {% if m.operating_cash_flow.yoy_change_pct is none %}Not reported{% else %}{% if m.operating_cash_flow.yoy_change_pct >= 0 %}▲ {% else %}▼ {% endif %}{{ m.operating_cash_flow.change_display }} YoY{% endif %}
                </div>
            </div>
        </div>

        <!-- Interactive Charts Row -->
        <div class="charts-row">
            <div class="card">
                <div class="section-title">📊 Financial Performance Comparison (YoY in $M)</div>
                <div class="chart-container">
                    <canvas id="financialsChart"></canvas>
                </div>
            </div>
            <div class="card">
                <div class="section-title">⚠️ Item 1A Risk Factor Matrix</div>
                <div class="chart-container">
                    <canvas id="riskChart"></canvas>
                </div>
            </div>
        </div>

        <!-- Executive Summary -->
        <div class="card exec-card">
            <div class="section-title">💡 Executive Summary & Strategic Guidance</div>
            <p><strong>Analyst Sentiment:</strong> <span style="color: var(--accent-green); font-weight: 700;">{{ e.sentiment_label }}</span></p>
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

        <!-- Risk Factor Cards -->
        <div class="section-title">🛡️ Detailed Item 1A Risk Assessment</div>
        <div class="risk-grid">
            {% for risk in r.risk_factors %}
            <div class="risk-card severity-{{ risk.severity }}">
                <div class="risk-header">
                    <span style="font-weight: 700; color: #fff; font-size: 1.05rem;">{{ risk.title }}</span>
                    <span class="severity-tag">{{ risk.severity }}</span>
                </div>
                <p style="font-size: 0.85rem; color: var(--text-muted); margin-bottom: 0.5rem;"><strong>Category:</strong> {{ risk.category }}</p>
                <p style="font-size: 0.92rem; color: #cbd5e1; margin-bottom: 0.6rem;">{{ risk.summary }}</p>
                {% if risk.mitigation_strategy %}
                <p style="font-size: 0.85rem; color: var(--accent-cyan);"><strong>Mitigation:</strong> {{ risk.mitigation_strategy }}</p>
                {% endif %}
            </div>
            {% endfor %}
        </div>
    </div>

    <!-- Chart.js Setup Scripts -->
    <script>
        // Financials YoY Bar Chart
        const ctxFin = document.getElementById('financialsChart').getContext('2d');
        new Chart(ctxFin, {
            type: 'bar',
            data: {
                labels: ['Revenue', 'Operating Expenses', 'Net Income', 'Operating Cash Flow'],
                datasets: [
                    {
                        label: 'FY{{ m.prior_fiscal_year }} ($M)',
                        data: [{{ m.revenue.chart_prior }}, {{ m.operating_expenses.chart_prior }}, {{ m.net_income.chart_prior }}, {{ m.operating_cash_flow.chart_prior }}],
                        backgroundColor: 'rgba(148, 163, 184, 0.4)',
                        borderColor: 'rgba(148, 163, 184, 0.8)',
                        borderWidth: 1,
                        borderRadius: 6
                    },
                    {
                        label: 'FY{{ m.fiscal_year }} ($M)',
                        data: [{{ m.revenue.chart_current }}, {{ m.operating_expenses.chart_current }}, {{ m.net_income.chart_current }}, {{ m.operating_cash_flow.chart_current }}],
                        backgroundColor: 'rgba(56, 189, 248, 0.8)',
                        borderColor: 'rgba(56, 189, 248, 1)',
                        borderWidth: 1,
                        borderRadius: 6
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { labels: { color: '#94a3b8', font: { family: 'Inter' } } }
                },
                scales: {
                    x: { ticks: { color: '#94a3b8' }, grid: { color: 'rgba(255, 255, 255, 0.05)' } },
                    y: { ticks: { color: '#94a3b8' }, grid: { color: 'rgba(255, 255, 255, 0.05)' } }
                }
            }
        });

        // Risk Factor Donut Chart
        const ctxRisk = document.getElementById('riskChart').getContext('2d');
        new Chart(ctxRisk, {
            type: 'doughnut',
            data: {
                labels: ['High Severity', 'Medium Severity', 'Low Severity'],
                datasets: [{
                    data: [{{ high_count }}, {{ med_count }}, {{ low_count }}],
                    backgroundColor: [
                        'rgba(239, 68, 68, 0.85)',
                        'rgba(245, 158, 11, 0.85)',
                        'rgba(16, 185, 129, 0.85)'
                    ],
                    borderColor: 'rgba(18, 24, 40, 1)',
                    borderWidth: 3
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { position: 'bottom', labels: { color: '#94a3b8', font: { family: 'Inter' } } }
                },
                cutout: '65%'
            }
        });
    </script>
</body>
</html>
"""
        template = Template(html_template)
        return template.render(
            r=r,
            m=m,
            e=e,
            high_count=high_count,
            med_count=med_count,
            low_count=low_count
        )
