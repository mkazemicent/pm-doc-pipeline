"""Harvest page metadata from Confluence — produces a link catalog, not content dumps."""

import json
import os
from datetime import datetime, timezone
from pathlib import Path

from .base import BaseHarvester


class ConfluenceHarvester(BaseHarvester):
    """Build a lightweight metadata catalog of Confluence pages.

    Instead of dumping full page HTML (which drifts from the source of truth),
    this harvester creates a searchable index with titles, links, labels, and
    last-modified dates. Copilot can use this to answer "where is the doc about X?"
    without duplicating Confluence content locally.

    For specific pages you *do* want full local copies of, use the `pinned_page_ids`
    config to selectively download content.
    """

    def __init__(self, config: dict, raw_dir: Path):
        super().__init__(config, raw_dir)
        self.source_cfg = config.get("sources", {}).get("confluence", {})

    def harvest(self) -> list[Path]:
        if not self.source_cfg.get("enabled"):
            self.log.info("Confluence source is disabled, skipping.")
            return []

        from atlassian import Confluence

        base_url = self.source_cfg["base_url"]
        username = os.environ.get("CONFLUENCE_USERNAME", "")
        token = os.environ.get("CONFLUENCE_API_TOKEN", "")

        if not username or not token:
            self.log.warning("Confluence credentials not set. Set CONFLUENCE_USERNAME and CONFLUENCE_API_TOKEN.")
            return []

        client = Confluence(url=base_url, username=username, password=token, cloud=True)
        max_pages = self.source_cfg.get("max_pages_per_space", 200)
        downloaded: list[Path] = []

        # ── Metadata catalog (lightweight index) ──
        catalog_entries: list[dict] = []

        for space in self.source_cfg.get("spaces", []):
            space_key = space["key"]
            label_filter = space.get("label_filter", [])
            self.log.info("Cataloging space: %s", space_key)

            start = 0
            while start < max_pages:
                results = client.get_all_pages_from_space(
                    space_key, start=start, limit=50,
                    expand="version,metadata.labels",
                )
                if not results:
                    break
                for page in results:
                    page_labels = [
                        lbl["name"]
                        for lbl in page.get("metadata", {}).get("labels", {}).get("results", [])
                    ]

                    # Apply label filter if configured
                    if label_filter and not any(lbl in label_filter for lbl in page_labels):
                        continue

                    version = page.get("version", {})
                    catalog_entries.append({
                        "page_id": page["id"],
                        "title": page["title"],
                        "space": space_key,
                        "url": f"{base_url}/pages/{page['id']}",
                        "labels": page_labels,
                        "last_modified": version.get("when", ""),
                        "last_author": version.get("by", {}).get("displayName", ""),
                        "version": version.get("number", 0),
                    })

                start += len(results)

        # Write the catalog as a Markdown file Copilot can search
        if catalog_entries:
            catalog_md = self._render_catalog(catalog_entries, base_url)
            downloaded.append(
                self._write_raw("confluence_catalog.md", catalog_md, subdir="confluence")
            )
            # Also write raw JSON for programmatic use
            downloaded.append(
                self._write_raw(
                    "confluence_catalog.json",
                    json.dumps(catalog_entries, indent=2),
                    subdir="confluence",
                )
            )

        # ── Pinned pages (full content for specific high-value pages) ──
        export_fmt = self.source_cfg.get("export_format", "storage")
        for page_id in self.source_cfg.get("pinned_page_ids", []):
            self.log.info("Fetching pinned page: %s", page_id)
            page = client.get_page_by_id(page_id, expand=f"body.{export_fmt},version")
            html = page["body"][export_fmt]["value"]
            title = page["title"].replace("/", "_").replace(" ", "_")
            fname = f"pinned_{page_id}_{title}.html"
            downloaded.append(self._write_raw(fname, html, subdir="confluence"))

        self.log.info("Confluence: cataloged %d pages, fetched %d pinned pages.",
                       len(catalog_entries), len(self.source_cfg.get("pinned_page_ids", [])))
        return downloaded

    @staticmethod
    def _render_catalog(entries: list[dict], base_url: str) -> str:
        """Render the catalog as a searchable Markdown document."""
        now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        lines = [
            "---",
            "title: \"Confluence Page Catalog\"",
            "source: \"confluence\"",
            f"date_harvested: \"{now}\"",
            "type: \"catalog\"",
            "---",
            "",
            "# Confluence Page Catalog",
            "",
            f"_Last synced: {now}_  ",
            f"_Source: {base_url}_  ",
            f"_Total pages indexed: {len(entries)}_",
            "",
            "Use this catalog to find where docs live in Confluence.",
            "Pinned pages have full local copies; everything else links back to Confluence.",
            "",
        ]

        # Group by space
        by_space: dict[str, list[dict]] = {}
        for entry in entries:
            by_space.setdefault(entry["space"], []).append(entry)

        for space_key, pages in sorted(by_space.items()):
            lines.append(f"## Space: {space_key}")
            lines.append("")
            lines.append("| Title | Labels | Last Modified | Author | Link |")
            lines.append("|---|---|---|---|---|")
            for p in sorted(pages, key=lambda x: x["title"]):
                labels = ", ".join(p["labels"]) if p["labels"] else "-"
                modified = p["last_modified"][:10] if p["last_modified"] else "-"
                author = p["last_author"] or "-"
                lines.append(
                    f"| {p['title']} | {labels} | {modified} | {author} | [Open]({p['url']}) |"
                )
            lines.append("")

        return "\n".join(lines)
