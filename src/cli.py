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
@click.option("--force", "-f", is_flag=True, help="Force reprocessing of all files.")
@click.pass_context
def run(ctx, stage, force):
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

    run_pipeline(config_path, project_root, stages, force=force)
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
@click.option("--output", "-o", default=None, type=click.Path(), help="Output file path.")
@click.pass_context
def report(ctx, output):
    """Generate a weekly report from pipeline output artifacts."""
    from .engine.report import WeeklyReportGenerator

    project_root = ctx.obj["project_root"]
    config = load_config(ctx.obj["config_path"])
    output_dir = project_root / config.get("general", {}).get("output_dir", "output")

    if not (output_dir / "PROJECT_CONTEXT.md").exists():
        click.echo("Error: No output artifacts found. Run 'pm-pipeline run' first.", err=True)
        sys.exit(1)

    generator = WeeklyReportGenerator(output_dir)
    output_path = Path(output).resolve() if output else None
    result = generator.write(output_path)
    click.echo(f"Report generated: {result}")


@cli.command()
@click.argument("query")
@click.option("--case-sensitive", "-cs", is_flag=True, help="Case-sensitive search.")
@click.pass_context
def search(ctx, query, case_sensitive):
    """Search the knowledge base for a keyword or phrase.

    Examples:
      pm-pipeline search "auth feature"
      pm-pipeline search PROJ-123
      pm-pipeline search "roadmap" --case-sensitive
    """
    from .engine.search import KnowledgeBaseSearch

    project_root = ctx.obj["project_root"]
    config = load_config(ctx.obj["config_path"])
    output_dir = project_root / config.get("general", {}).get("output_dir", "output")

    if not output_dir.exists():
        click.echo("Error: No output directory found. Run 'pm-pipeline run' first.", err=True)
        sys.exit(1)

    searcher = KnowledgeBaseSearch(output_dir)
    results = searcher.search(query, case_sensitive=case_sensitive)
    click.echo(searcher.format_results(results))


@cli.command()
@click.argument("directory", type=click.Path(exists=True))
@click.option("--interval", "-i", default=30, help="Poll interval in seconds.")
@click.pass_context
def watch(ctx, directory, interval):
    """Watch a directory and auto-process new/changed files.

    Polls the directory for supported file types. When changes are detected,
    automatically stages and runs the pipeline.

    Examples:
      pm-pipeline watch ~/Documents/pm-docs
      pm-pipeline watch ~/Downloads --interval 60
    """
    from .watcher import PipelineWatcher

    config_path = ctx.obj["config_path"]
    project_root = ctx.obj["project_root"]
    config = load_config(config_path)
    raw_dir = project_root / config.get("general", {}).get("raw_dir", "raw")

    watch_dir = Path(directory).resolve()
    watcher = PipelineWatcher(watch_dir, config_path, project_root)

    def on_change(changed_files):
        click.echo(f"\n--- {len(changed_files)} file(s) changed ---")
        harvester = LocalHarvester(config, raw_dir, project_root)
        for changed_file in changed_files:
            try:
                result = harvester.stage_file(changed_file)
                if result["status"] == "staged":
                    click.echo(f"  + Staged: {changed_file.name}")
                else:
                    click.echo(f"  ~ Already staged: {changed_file.name}")
            except (FileNotFoundError, ValueError) as exc:
                click.echo(f"  ! Skipped: {exc}")
                continue

        click.echo("  Running pipeline...")
        try:
            run_pipeline(config_path, project_root)
            click.echo("  Done. Output updated.")
        except Exception as exc:
            click.echo(f"  ! Pipeline error: {exc}")

    click.echo(f"Watching: {watch_dir}")
    click.echo(f"Interval: {interval}s")
    click.echo("Ctrl+C to stop.\n")
    watcher.run_loop(interval=interval, on_change=on_change)


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
