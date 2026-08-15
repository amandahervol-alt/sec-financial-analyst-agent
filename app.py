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


def run_pipeline(sample_file: str, company_name: str, serve: bool = True):
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass

    print(f"\n[+] Launching SEC Financial Analyst Agent...")
    file_path = Path(sample_file)

    if not file_path.exists():
        print(f"[!] File not found: {sample_file}")
        sys.exit(1)

    with open(file_path, "r", encoding="utf-8") as f:
        raw_text = f.read()

    print(f"[*] Parsing filing document for '{company_name}'...")
    parser = SECParser(raw_text)
    sections = parser.extract_sections()

    print(f"[*] Agent Analyzing Item 1A Risk Factors & Item 7 MD&A Metrics...")
    agent = SECFinancialAnalystAgent()
    report = agent.analyze(company_name, sections)

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

    print(f"\n[OK] Analysis Complete!")
    print(f"[+] Markdown Report generated: {md_file.resolve()}")
    print(f"[+] HTML Dashboard generated: {html_file.resolve()}")
    print(f"[+] Financial Health Score: {report.executive_summary.overall_health_score}/10 ({report.executive_summary.sentiment_label})")

    if serve:
        print("\n🌐 Launching local HTTP dashboard server at http://localhost:8000 ...")
        os.chdir(output_dir)
        handler = http.server.SimpleHTTPRequestHandler
        socketserver.TCPServer.allow_reuse_address = True
        try:
            with socketserver.TCPServer(("", 8000), handler) as httpd:
                webbrowser.open("http://localhost:8000/dashboard.html")
                print("Press Ctrl+C to stop the dashboard server.")
                httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nServer stopped.")


def main():
    parser = argparse.ArgumentParser(description="SEC 10-K & Earnings Call Financial Analyst Agent")
    parser.add_argument("--file", type=str, default="data/samples/sample_10k_techcorp.txt", help="Path to 10-K text file")
    parser.add_argument("--company", type=str, default="TechCorp Solutions Inc.", help="Company Name")
    parser.add_argument("--no-serve", action="store_true", help="Do not launch HTTP server")

    args = parser.parse_args()
    run_pipeline(args.file, args.company, serve=not args.no_serve)


if __name__ == "__main__":
    main()
