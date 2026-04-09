"""Harvest issue/PR metadata from GitHub — produces a catalog + selective full content."""

import json
import os
from datetime import datetime
from pathlib import Path

from .base import BaseHarvester


class GitHubHarvester(BaseHarvester):
    """Build a metadata catalog of GitHub issues and PRs.

    Produces a searchable Markdown index. Only issues/PRs matching your label
    filters get full content downloaded (body + comments). The rest appear as
    one-line entries with links back to GitHub.
    """

    def __init__(self, config: dict, raw_dir: Path):
        super().__init__(config, raw_dir)
        self.source_cfg = config.get("sources", {}).get("github", {})

    def harvest(self) -> list[Path]:
        if not self.source_cfg.get("enabled"):
            self.log.info("GitHub source is disabled, skipping.")
            return []

        from github import Github

        token = os.environ.get("GITHUB_TOKEN", "")
        if not token:
            self.log.warning("GITHUB_TOKEN not set.")
            return []

        gh = Github(token)
        downloaded: list[Path] = []

        for repo_cfg in self.source_cfg.get("repos", []):
            owner = repo_cfg["owner"]
            repo_name = repo_cfg["repo"]
            self.log.info("Cataloging: %s/%s", owner, repo_name)
            repo = gh.get_repo(f"{owner}/{repo_name}")

            since = repo_cfg.get("since")
            since_dt = datetime.fromisoformat(since) if since else None
            state = repo_cfg.get("state", "all")
            labels_filter = set(repo_cfg.get("labels_filter", []))

            catalog: list[dict] = []
            pinned_items: list[dict] = []

            # Issues
            if repo_cfg.get("fetch_issues", True):
                kwargs = {"state": state}
                if since_dt:
                    kwargs["since"] = since_dt
                for issue in repo.get_issues(**kwargs):
                    if issue.pull_request:
                        continue

                    issue_labels = {lbl.name for lbl in issue.labels}
                    entry = {
                        "type": "issue",
                        "number": issue.number,
                        "title": issue.title,
                        "state": issue.state,
                        "labels": list(issue_labels),
                        "created_at": issue.created_at.isoformat(),
                        "updated_at": issue.updated_at.isoformat(),
                        "url": issue.html_url,
                    }
                    catalog.append(entry)

                    # Full content only for label-matched items
                    if labels_filter and issue_labels & labels_filter:
                        entry["body"] = issue.body or ""
                        entry["comments"] = [
                            {"author": c.user.login, "body": c.body, "date": c.created_at.isoformat()}
                            for c in issue.get_comments()
                        ]
                        pinned_items.append(entry)

            # Pull Requests
            if repo_cfg.get("fetch_pull_requests", True):
                for pr in repo.get_pulls(state=state):
                    if since_dt and pr.updated_at < since_dt:
                        continue
                    pr_labels = {lbl.name for lbl in pr.labels}
                    entry = {
                        "type": "pr",
                        "number": pr.number,
                        "title": pr.title,
                        "state": pr.state,
                        "labels": list(pr_labels),
                        "merged": pr.merged,
                        "created_at": pr.created_at.isoformat(),
                        "updated_at": pr.updated_at.isoformat(),
                        "url": pr.html_url,
                    }
                    catalog.append(entry)

                    if labels_filter and pr_labels & labels_filter:
                        entry["body"] = pr.body or ""
                        pinned_items.append(entry)

            # Write catalog
            if catalog:
                catalog_md = self._render_catalog(catalog, owner, repo_name)
                downloaded.append(
                    self._write_raw(f"github_{repo_name}_catalog.md", catalog_md, subdir="github")
                )

            # Write pinned items with full content
            for item in pinned_items:
                fname = f"{item['type']}_{item['number']}.json"
                downloaded.append(
                    self._write_raw(fname, json.dumps(item, indent=2), subdir=f"github/{repo_name}")
                )

            self.log.info("GitHub %s/%s: cataloged %d items, pinned %d.",
                          owner, repo_name, len(catalog), len(pinned_items))

        return downloaded

    @staticmethod
    def _render_catalog(entries: list[dict], owner: str, repo_name: str) -> str:
        now = datetime.now().strftime("%Y-%m-%d %H:%M UTC")
        lines = [
            "---",
            f"title: \"GitHub Catalog — {owner}/{repo_name}\"",
            "source: \"github\"",
            f"date_harvested: \"{now}\"",
            "type: \"catalog\"",
            "---",
            "",
            f"# GitHub: {owner}/{repo_name}",
            "",
            f"_Last synced: {now}_  ",
            f"_Items indexed: {len(entries)}_",
            "",
        ]

        issues = [e for e in entries if e["type"] == "issue"]
        prs = [e for e in entries if e["type"] == "pr"]

        if issues:
            lines.append("## Issues")
            lines.append("")
            lines.append("| # | Title | State | Labels | Updated | Link |")
            lines.append("|---|---|---|---|---|---|")
            for e in sorted(issues, key=lambda x: x["number"], reverse=True):
                labels = ", ".join(e["labels"]) if e["labels"] else "-"
                updated = e["updated_at"][:10]
                lines.append(
                    f"| {e['number']} | {e['title']} | {e['state']} | {labels} | {updated} | [Open]({e['url']}) |"
                )
            lines.append("")

        if prs:
            lines.append("## Pull Requests")
            lines.append("")
            lines.append("| # | Title | State | Merged | Labels | Updated | Link |")
            lines.append("|---|---|---|---|---|---|---|")
            for e in sorted(prs, key=lambda x: x["number"], reverse=True):
                labels = ", ".join(e["labels"]) if e["labels"] else "-"
                updated = e["updated_at"][:10]
                merged = "Yes" if e.get("merged") else "No"
                lines.append(
                    f"| {e['number']} | {e['title']} | {e['state']} | {merged} | {labels} | {updated} | [Open]({e['url']}) |"
                )
            lines.append("")

        return "\n".join(lines)
