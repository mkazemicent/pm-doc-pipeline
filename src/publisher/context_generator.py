"""Generate PROJECT_CONTEXT.md — the single file Copilot always finds."""

import logging
from datetime import datetime, timezone
from pathlib import Path

log = logging.getLogger(__name__)


class ContextGenerator:
    """Build a unified PROJECT_CONTEXT.md that summarizes the entire knowledge base.

    This file is the primary entry point for Copilot. It contains:
    - A list of all processed documents with one-line summaries
    - All extracted decisions (inline, not in a separate file)
    - All detected ticket references
    - Recent changes
    - Links to Confluence/GitHub catalogs

    Keeping everything in one file means Copilot can always find it.
    """

    def __init__(self, config: dict):
        self.config = config
        self.project_name = config.get("general", {}).get("project_name", "My Project")

    def generate(
        self,
        processed_files: list[Path],
        decisions: list,
        changes: list,
        output_dir: Path,
    ) -> Path:
        now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        lines = [
            "---",
            f"title: \"{self.project_name} — Knowledge Base\"",
            f"last_updated: \"{now}\"",
            f"document_count: {len(processed_files)}",
            f"decision_count: {len(decisions)}",
            "---",
            "",
            f"# {self.project_name} — Project Context",
            "",
            f"_Auto-generated: {now}_  ",
            f"_Documents: {len(processed_files)} | Decisions: {len(decisions)} | Changes: {len(changes)}_",
            "",
            "---",
            "",
        ]

        # ── Document inventory ──
        lines.append("## Documents")
        lines.append("")
        if processed_files:
            # Group by source type
            by_source = self._group_by_source(processed_files)
            for source, files in sorted(by_source.items()):
                lines.append(f"### {source.title()} ({len(files)} files)")
                lines.append("")
                for f in sorted(files, key=lambda x: x.name):
                    # Extract title from frontmatter if possible
                    title = self._extract_title(f)
                    preview = self._extract_preview(f)
                    lines.append(f"- **{title}** — `{f.name}`")
                    if preview:
                        # Indent preview as a quote block for readability
                        preview_oneline = preview.replace("\n", " ").strip()
                        if len(preview_oneline) > 200:
                            preview_oneline = preview_oneline[:200].rsplit(" ", 1)[0] + "..."
                        lines.append(f"  > {preview_oneline}")
                lines.append("")
        else:
            lines.append("_No documents processed yet. Run `pm-pipeline add <file>` then `pm-pipeline run`._")
            lines.append("")

        # ── Decisions ──
        lines.append("## Decisions")
        lines.append("")
        if decisions:
            for i, dec in enumerate(decisions, 1):
                source_short = Path(dec.source_file).name
                kw = ", ".join(dec.keywords_matched)
                tickets = f" [{', '.join(dec.tickets)}]" if dec.tickets else ""
                lines.append(f"### Decision #{i}{tickets}")
                lines.append(f"_Source: {source_short} | Keywords: {kw}_")
                lines.append("")
                lines.append("> " + dec.context.replace("\n", "\n> "))
                lines.append("")
        else:
            lines.append("_No decisions detected yet._")
            lines.append("")

        # ── Ticket references ──
        all_tickets: set[str] = set()
        for dec in decisions:
            all_tickets.update(dec.tickets)
        for chg in changes:
            all_tickets.update(chg.tickets)

        if all_tickets:
            lines.append("## Ticket References")
            lines.append("")
            for ticket in sorted(all_tickets):
                lines.append(f"- {ticket}")
            lines.append("")

        # ── Cross-references (which docs share tickets) ──
        if all_tickets:
            ticket_to_docs: dict[str, list[str]] = {}
            for dec in decisions:
                doc_name = Path(dec.source_file).name
                for ticket in dec.tickets:
                    ticket_to_docs.setdefault(ticket, []).append(doc_name)
            for chg in changes:
                doc_name = chg.filepath.name
                for ticket in chg.tickets:
                    ticket_to_docs.setdefault(ticket, []).append(doc_name)

            # Only show tickets that appear in multiple documents
            cross_refs = {t: list(set(docs)) for t, docs in ticket_to_docs.items() if len(set(docs)) > 1}
            if cross_refs:
                lines.append("## Cross-References")
                lines.append("")
                lines.append("Tickets referenced across multiple documents:")
                lines.append("")
                for ticket, docs in sorted(cross_refs.items()):
                    lines.append(f"- **{ticket}**: {', '.join(sorted(docs))}")
                lines.append("")

        # ── Recent changes ──
        lines.append("## Recent Changes")
        lines.append("")
        if changes:
            for chg in changes[:20]:  # cap at 20 most recent
                icon = {"added": "+", "modified": "~", "deleted": "-"}.get(chg.change_type, "?")
                tickets = f" [{', '.join(chg.tickets)}]" if chg.tickets else ""
                lines.append(f"- `[{icon}]` {chg.filepath.name}{tickets}")
            if len(changes) > 20:
                lines.append(f"- _...and {len(changes) - 20} more (see CHANGELOG.md)_")
            lines.append("")
        else:
            lines.append("_No changes detected._")
            lines.append("")

        # Write
        output_dir.mkdir(parents=True, exist_ok=True)
        ctx_path = output_dir / "PROJECT_CONTEXT.md"
        ctx_path.write_text("\n".join(lines), encoding="utf-8")
        log.info("Generated PROJECT_CONTEXT.md (%d lines)", len(lines))
        return ctx_path

    @staticmethod
    def _group_by_source(files: list[Path]) -> dict[str, list[Path]]:
        groups: dict[str, list[Path]] = {}
        for f in files:
            source = "local"
            for marker in ("confluence", "github", "webex"):
                if marker in str(f):
                    source = marker
                    break
            groups.setdefault(source, []).append(f)
        return groups

    @staticmethod
    def _extract_title(filepath: Path) -> str:
        """Try to read the title from YAML frontmatter, fall back to filename."""
        try:
            with open(filepath, encoding="utf-8") as f:
                first_line = f.readline().strip()
                if first_line == "---":
                    for line in f:
                        line = line.strip()
                        if line == "---":
                            break
                        if line.startswith("title:"):
                            title = line.split(":", 1)[1].strip().strip('"').strip("'")
                            if title:
                                return title
        except Exception:
            pass
        return filepath.stem.replace("_", " ").replace("-", " ").title()

    @staticmethod
    def _extract_preview(filepath: Path, max_chars: int = 500) -> str:
        """Extract the first ~500 chars of document body, skipping frontmatter."""
        try:
            text = filepath.read_text(encoding="utf-8", errors="replace")
            lines = text.splitlines()

            # Skip YAML frontmatter
            body_start = 0
            if lines and lines[0].strip() == "---":
                for i, line in enumerate(lines[1:], 1):
                    if line.strip() == "---":
                        body_start = i + 1
                        break

            body = "\n".join(lines[body_start:]).strip()
            if len(body) > max_chars:
                # Cut at last word boundary before max_chars
                body = body[:max_chars].rsplit(" ", 1)[0] + "..."
            return body
        except Exception:
            return ""
