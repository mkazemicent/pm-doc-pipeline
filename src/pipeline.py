"""Core pipeline orchestrator — ties all four stages together."""

import logging
from pathlib import Path

import yaml

from .harvester import ConfluenceHarvester, GitHubHarvester, WebexHarvester
from .harvester.local_harvester import LocalHarvester
from .translator import UniversalTranslator
from .engine import ChangeTracker, DecisionLogBuilder, ChangelogGenerator
from .publisher import Publisher, ContextGenerator

log = logging.getLogger(__name__)


def load_config(config_path: Path) -> dict:
    """Load and return the pipeline YAML configuration."""
    with open(config_path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def run_pipeline(config_path: Path, project_root: Path, stages: list[str] | None = None):
    """Execute the full pipeline or specific stages.

    Args:
        config_path: Path to pipeline.yaml
        project_root: Root directory of the project
        stages: Optional list of stages to run. Defaults to all.
                 Valid: "harvest", "translate", "engine", "publish"
    """
    config = load_config(config_path)

    raw_dir = project_root / config.get("general", {}).get("raw_dir", "raw")
    processed_dir = project_root / config.get("general", {}).get("processed_dir", "processed")
    output_dir = project_root / config.get("general", {}).get("output_dir", "output")

    run_all = stages is None
    stages_set = set(stages or [])

    all_raw_files: list[Path] = []
    all_processed_files: list[Path] = []

    # ── Stage 1: Harvest ──
    if run_all or "harvest" in stages_set:
        log.info("=" * 60)
        log.info("STAGE 1: DATA HARVESTER")
        log.info("=" * 60)

        # Remote catalogs
        for harvester in [
            ConfluenceHarvester(config, raw_dir),
            GitHubHarvester(config, raw_dir),
            WebexHarvester(config, raw_dir),
        ]:
            all_raw_files.extend(harvester.harvest())

        # Local staged files
        local = LocalHarvester(config, raw_dir, project_root)
        all_raw_files.extend(local.harvest())

        log.info("Harvest complete: %d raw files.", len(all_raw_files))
    else:
        # Collect existing raw files for downstream stages
        if raw_dir.exists():
            all_raw_files = [f for f in raw_dir.rglob("*") if f.is_file()]

    # ── Stage 2: Translate ──
    if run_all or "translate" in stages_set:
        log.info("=" * 60)
        log.info("STAGE 2: UNIVERSAL TRANSLATOR")
        log.info("=" * 60)

        translator = UniversalTranslator(config, processed_dir)
        all_processed_files = translator.translate(all_raw_files)

        log.info("Translation complete: %d processed files.", len(all_processed_files))
    else:
        if processed_dir.exists():
            all_processed_files = [f for f in processed_dir.rglob("*.md") if f.is_file()]

    # ── Stage 3: Engine ──
    decisions = []
    changes = []
    decision_log_md = ""
    changelog_md = ""

    if run_all or "engine" in stages_set:
        log.info("=" * 60)
        log.info("STAGE 3: THE ENGINE")
        log.info("=" * 60)

        tracker = ChangeTracker(config, project_root)
        changes = tracker.detect_changes(processed_dir)

        decision_builder = DecisionLogBuilder(config)
        decisions = decision_builder.scan(all_processed_files)
        decision_log_md = decision_builder.render(decisions)

        cl_gen = ChangelogGenerator(config)
        changelog_md = cl_gen.generate(changes)

        log.info("Engine complete: %d changes, %d decisions.", len(changes), len(decisions))

    # ── Stage 4: Publish ──
    if run_all or "publish" in stages_set:
        log.info("=" * 60)
        log.info("STAGE 4: THE PUBLISHER")
        log.info("=" * 60)

        # Load existing logs if engine was skipped
        if not decision_log_md:
            dec_file = output_dir / "DECISION_LOG.md"
            decision_log_md = dec_file.read_text(encoding="utf-8") if dec_file.exists() else "# Decision Log\n\n_No decisions processed._\n"
        if not changelog_md:
            cl_file = output_dir / "CHANGELOG.md"
            changelog_md = cl_file.read_text(encoding="utf-8") if cl_file.exists() else "# Changelog\n\n_No changes processed._\n"

        # Publish docs
        publisher = Publisher(config, output_dir)
        publisher.publish(all_processed_files, decision_log_md, changelog_md)

        # Generate PROJECT_CONTEXT.md (the single file Copilot always uses)
        ctx_gen = ContextGenerator(config)
        ctx_gen.generate(all_processed_files, decisions, changes, output_dir)

        log.info("Publish complete.")

    log.info("=" * 60)
    log.info("PIPELINE FINISHED")
    log.info("=" * 60)
