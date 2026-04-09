from click.testing import CliRunner

from src.cli import cli


TEST_CONFIG_YAML = """
general:
  project_name: Test
  raw_dir: raw
  processed_dir: processed
  output_dir: output
engine:
  ticket_patterns:
    - "[A-Z]{2,10}-\\\\d+"
    - "#\\\\d+"
  decision_keywords:
    - "decided"
    - "approved"
    - "action item"
  changelog:
    group_by: source
    max_entries: 100
"""


def test_cli_status_returns_zero(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    config_dir = tmp_path / "config"
    config_dir.mkdir(parents=True, exist_ok=True)
    config_path = config_dir / "pipeline.yaml"
    config_path.write_text(TEST_CONFIG_YAML, encoding="utf-8")

    runner = CliRunner()
    result = runner.invoke(cli, ["--config", str(config_path), "status"])

    assert result.exit_code == 0
    assert "PM Doc Pipeline" in result.output


def test_cli_init_creates_required_directories(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    config_dir = tmp_path / "config"
    config_dir.mkdir(parents=True, exist_ok=True)
    config_path = config_dir / "pipeline.yaml"
    config_path.write_text(TEST_CONFIG_YAML, encoding="utf-8")

    runner = CliRunner()
    result = runner.invoke(cli, ["--config", str(config_path), "init"])

    assert result.exit_code == 0
    assert (tmp_path / "raw" / "local").exists()
    assert (tmp_path / "processed").exists()
    assert (tmp_path / "output").exists()
    assert (tmp_path / "config").exists()


def test_cli_list_empty_manifest_shows_helpful_message(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    config_dir = tmp_path / "config"
    config_dir.mkdir(parents=True, exist_ok=True)
    config_path = config_dir / "pipeline.yaml"
    config_path.write_text(TEST_CONFIG_YAML, encoding="utf-8")

    runner = CliRunner()
    result = runner.invoke(cli, ["--config", str(config_path), "list"])

    assert result.exit_code == 0
    assert "No files staged. Use 'pm-pipeline add <file>' to stage documents." in result.output
