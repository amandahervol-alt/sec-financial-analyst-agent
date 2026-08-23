import os
import sys
import argparse
import webbrowser
import http.server
import socketserver
from pathlib import Path

from src.sec_parser import SECParser
from src.financial_agent import SECFinancialAnalystAgent
from src.report_generator import ReportGenerator

SAMPLE_MAP = {
    "techcorp": ("data/samples/sample_10k_techcorp.txt", "TechCorp Solutions Inc."),
    "healthplus": ("data/samples/sample_10k_healthplus.txt", "HealthPlus Therapeutics Inc."),
    "retailhub": ("data/samples/sample_10k_retailhub.txt", "RetailHub Global Inc.")
}


def run_pipeline(sample_file: str, company_name: str, serve: bool = True):
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass

    print(f"\n============================================================")
    print(f"📈 Launching Autonomous SEC Financial Analyst Agent")
    print(f"============================================================")
    file_path = Path(sample_file)

    if not file_path.exists():
        print(f"[!] Filing document not found: {sample_file}")
        sys.exit(1)

    with open(file_path, "r", encoding="utf-8") as f:
        raw_text = f.read()

    print(f"\n[*] [1/3] Parsing filing document for '{company_name}'...")
    parser = SECParser(raw_text)
    sections = parser.extract_sections()

    print(f"[*] [2/3] Analyzing MD&A Financial Metrics & Item 1A Risk Factors...")
    agent = SECFinancialAnalystAgent()
    report = agent.analyze(company_name, sections)

    print(f"[*] [3/3] Generating Executive Markdown & Chart.js Dashboard...")
    generator = ReportGenerator(report)
    markdown_out = generator.generate_markdown()
    html_out = generator.generate_html()

    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)

    md_file = output_dir / "report.md"
    html_file = output_dir / "dashboard.html"

    with open(md_file, "w", encoding="utf-8") as f:
        f.write(markdown_out)

    with open(html_file, "w", encoding="utf-8") as f:
        f.write(html_out)

    print(f"\n" + "=" * 60)
    print(f"✅ Analysis Complete for {company_name}")
    print(f"============================================================")
    print(f"[+] Health Score:     {report.executive_summary.overall_health_score}/10 ({report.executive_summary.sentiment_label})")
    print(f"[+] Revenue (YoY):    ${report.metrics.revenue.current_year_val}M ({'+' if report.metrics.revenue.yoy_change_pct > 0 else ''}{report.metrics.revenue.yoy_change_pct}%)")
    print(f"[+] Net Income (YoY): ${report.metrics.net_income.current_year_val}M ({'+' if report.metrics.net_income.yoy_change_pct > 0 else ''}{report.metrics.net_income.yoy_change_pct}%)")
    print(f"[+] Risk Factors:     {len(report.risk_factors)} identified and ranked")
    print(f"[+] Markdown Report:  {md_file.resolve()}")
    print(f"[+] HTML Dashboard:   {html_file.resolve()}")
    print(f"============================================================\n")

    if serve:
        print("🌐 Launching local HTTP dashboard server at http://localhost:8000/dashboard.html ...")
        os.chdir(output_dir)
        handler = http.server.SimpleHTTPRequestHandler
        socketserver.TCPServer.allow_reuse_address = True
        try:
            with socketserver.TCPServer(("", 8000), handler) as httpd:
                webbrowser.open("http://localhost:8000/dashboard.html")
                print("Dashboard active! Press Ctrl+C to stop.")
                httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nServer stopped.")


def main():
    parser = argparse.ArgumentParser(description="SEC 10-K Financial Analyst Agent CLI")
    parser.add_argument("--sample", choices=["techcorp", "healthplus", "retailhub"], default="techcorp", help="Choose a pre-loaded sample sector")
    parser.add_argument("--file", type=str, default=None, help="Custom path to 10-K text file")
    parser.add_argument("--company", type=str, default=None, help="Company Name")
    parser.add_argument("--no-serve", action="store_true", help="Generate reports without opening local web server")

    args = parser.parse_args()

    if args.file:
        sample_file = args.file
        company_name = args.company or Path(args.file).stem.replace("_", " ").title()
    else:
        sample_file, company_name = SAMPLE_MAP[args.sample]
        if args.company:
            company_name = args.company

    run_pipeline(sample_file, company_name, serve=not args.no_serve)


if __name__ == "__main__":
    main()
