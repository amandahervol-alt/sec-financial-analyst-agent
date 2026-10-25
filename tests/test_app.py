import pytest

import app
from tests.conftest import ROOT


def test_run_pipeline_writes_markdown_and_dashboard(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    app.run_pipeline(str(ROOT / "data/samples/sample_10k_retailhub.txt"), "RetailHub Global Inc.", serve=False)

    md = (tmp_path / "output/report.md").read_text(encoding="utf-8")
    html = (tmp_path / "output/dashboard.html").read_text(encoding="utf-8")
    assert "RetailHub Global Inc." in md
    assert "<!DOCTYPE html>" in html
    out = capsys.readouterr().out
    assert "Health Score:     8.4/10 (Bullish)" in out
    assert "Revenue (YoY):    $3250.0M (+14.4%)" in out


def test_missing_filing_exits_with_error(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    with pytest.raises(SystemExit) as exc:
        app.run_pipeline(str(tmp_path / "missing.txt"), "Nobody", serve=False)
    assert exc.value.code == 1


@pytest.mark.parametrize("sample", ["techcorp", "healthplus", "retailhub"])
def test_cli_samples_run_without_server(tmp_path, monkeypatch, sample):
    calls = {}
    monkeypatch.setattr(app, "run_pipeline", lambda f, c, serve: calls.update(file=f, company=c, serve=serve))
    monkeypatch.setattr("sys.argv", ["app.py", "--sample", sample, "--no-serve"])
    app.main()
    assert calls["file"].endswith(f"sample_10k_{sample}.txt")
    assert calls["serve"] is False


def test_cli_custom_file_derives_company_name(monkeypatch):
    calls = {}
    monkeypatch.setattr(app, "run_pipeline", lambda f, c, serve: calls.update(file=f, company=c))
    monkeypatch.setattr("sys.argv", ["app.py", "--file", "filings/acme_corp_10k.txt", "--no-serve"])
    app.main()
    assert calls["company"] == "Acme Corp 10K"
