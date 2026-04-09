"""CLI entry point for the PM Doc Pipeline."""

import logging
import sys
from pathlib import Path

import click

from .pipeline import run_pipeline, load_config
from .harvester.local_harvester import LocalHarvester

VALID_STAGES = ["harvest", "translate", "engine", "publish"]


@click.group()
@click.option("--config", "-c", default="config/pipeline.yaml", help="Path to pipeline config file.")
@click.option("--verbose", "-v", is_flag=True, help="Enable debug logging.")
@click.pass_context
def cli(ctx, config, verbose):
    """PM Doc Pipeline — Curated Doc-as-Code for Product Managers.

    Workflow:
      1. pm-pipeline add <file>     Stage a document for processing
      2. pm-pipeline run            Process staged files → clean Markdown
      3. Open output/ in VS Code    Let Copilot search your knowledge base
    """
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)-7s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )
    ctx.ensure_object(dict)
    ctx.obj["config_path"] = Path(config).resolve()
    ctx.obj["project_root"] = Path.cwd()


@cli.command()
@click.argument("files", nargs=-1, type=click.Path(exists=True))
@click.pass_context
def add(ctx, files):
    """Stage file(s) for processing.

    Examples:
      pm-pipeline add ~/docs/sprint-deck.pptx
      pm-pipeline add report.pdf meeting-notes.docx
    """
    if not files:
        click.echo("Usage: pm-pipeline add <file> [<file> ...]")
        return

    config = load_config(ctx.obj["config_path"])
    project_root = ctx.obj["project_root"]
    raw_dir = project_root / config.get("general", {}).get("raw_dir", "raw")
    harvester = LocalHarvester(config, raw_dir, project_root)

    for f in files:
        filepath = Path(f).resolve()
        try:
            result = harvester.stage_file(filepath)
            if result["status"] == "staged":
                click.echo(f"  + Staged: {filepath.name}")
            else:
                click.echo(f"  ~ Already staged: {filepath.name}")
        except (FileNotFoundError, ValueError) as exc:
            click.echo(f"  ! Error: {exc}", err=True)

    staged = harvester.list_staged()
    click.echo(f"\n{len(staged)} file(s) staged. Run 'pm-pipeline run' to process.")


@cli.command()
@click.argument("files", nargs=-1, type=click.Path())
@click.pass_context
def remove(ctx, files):
    """Remove file(s) from the staging manifest.

    Examples:
      pm-pipeline remove ~/docs/sprint-deck.pptx
    """
    if not files:
        click.echo("Usage: pm-pipeline remove <file> [<file> ...]")
        return

    config = load_config(ctx.obj["config_path"])
    project_root = ctx.obj["project_root"]
    raw_dir = project_root / config.get("general", {}).get("raw_dir", "raw")
    harvester = LocalHarvester(config, raw_dir, project_root)

    for f in files:
        filepath = Path(f).resolve()
        result = harvester.unstage_file(filepath)
        if result["status"] == "unstaged":
            click.echo(f"  - Removed: {filepath.name}")
        else:
            click.echo(f"  ? Not found in staging: {filepath.name}")


@cli.command(name="list")
@click.pass_context
def list_staged(ctx):
    """Show all staged files."""
    config = load_config(ctx.obj["config_path"])
    project_root = ctx.obj["project_root"]
    raw_dir = project_root / config.get("general", {}).get("raw_dir", "raw")
    harvester = LocalHarvester(config, raw_dir, project_root)

    staged = harvester.list_staged()
    if not staged:
        click.echo("No files staged. Use 'pm-pipeline add <file>' to stage documents.")
        return

    click.echo(f"Staged files ({len(staged)}):")
    click.echo("")
    for entry in staged:
        source = Path(entry["source"])
        exists = "ok" if source.exists() else "MISSING"
        click.echo(f"  [{exists:7s}] {source.name}")
        click.echo(f"           {entry['source']}")
        click.echo(f"           staged: {entry.get('staged_at', '?')}")
        click.echo("")


@cli.command()
@click.option(
    "--stage", "-s",
    multiple=True,
    type=click.Choice(VALID_STAGES, case_sensitive=False),
    help="Run specific stage(s). Omit to run all.",
)
@click.pass_context
def run(ctx, stage):
    """Run the pipeline (all stages or specific ones)."""
    config_path = ctx.obj["config_path"]
    project_root = ctx.obj["project_root"]

    if not config_path.exists():
        click.echo(f"Error: Config file not found: {config_path}", err=True)
        sys.exit(1)

    stages = list(stage) if stage else None
    stage_label = ", ".join(stages) if stages else "all"
    click.echo(f"Running pipeline stages: {stage_label}")
    click.echo(f"Config: {config_path}")
    click.echo()

    run_pipeline(config_path, project_root, stages)
    click.echo("\nDone. Open output/ in VS Code to explore with Copilot.")


@cli.command()
@click.pass_context
def status(ctx):
    """Show current pipeline status and file counts."""
    project_root = ctx.obj["project_root"]
    config = load_config(ctx.obj["config_path"])
    raw_dir = project_root / config.get("general", {}).get("raw_dir", "raw")

    # Staged files
    harvester = LocalHarvester(config, raw_dir, project_root)
    staged = harvester.list_staged()

    dirs = {
        "raw": project_root / "raw",
        "processed": project_root / "processed",
        "output": project_root / "output",
    }

    click.echo("PM Doc Pipeline — Status")
    click.echo("=" * 40)
    click.echo(f"  {'staged':12s}: {len(staged):4d} files")
    for name, path in dirs.items():
        if path.exists():
            count = sum(1 for f in path.rglob("*") if f.is_file())
            click.echo(f"  {name:12s}: {count:4d} files")
        else:
            click.echo(f"  {name:12s}:    -")

    # Check for PROJECT_CONTEXT.md
    ctx_file = project_root / "output" / "PROJECT_CONTEXT.md"
    if ctx_file.exists():
        click.echo(f"\n  Context file: {ctx_file} (exists)")
    click.echo()


@cli.command()
@click.pass_context
def init(ctx):
    """Initialize the project directory structure."""
    project_root = ctx.obj["project_root"]
    dirs = ["raw/local", "processed", "output", "config"]
    for d in dirs:
        (project_root / d).mkdir(parents=True, exist_ok=True)
    click.echo("Project directories initialized.")
    click.echo("Next: pm-pipeline add <file> to stage your first document.")


def main():
    cli()


if __name__ == "__main__":
    main()
