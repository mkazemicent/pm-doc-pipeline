# Copilot Instructions for PM Doc Pipeline

## Project Intent
This project builds a curated, local-first PM knowledge base that Copilot can query reliably.
Prioritize high-signal outputs over broad ingestion.

## Knowledge Base Usage
When answering questions about the project, its documents, decisions, or status:

1. **Always start with** `output/PROJECT_CONTEXT.md` — it contains the document inventory,
	all decisions, ticket references, cross-references, and recent changes.
2. **For document details**, read the specific file under `output/docs/`. Each file has
	YAML frontmatter with source and date metadata.
3. **For decision history**, check `output/DECISION_LOG.md` for the full list with
	source files, line numbers, and surrounding context.
4. **For recent changes**, check `output/CHANGELOG.md` for what changed in the last
	pipeline run.
5. **For weekly summaries**, check `output/reports/WEEKLY_REPORT.md` if it exists,
	or suggest the user run `pm-pipeline report` to generate one.
6. **For remote source lookups** (Confluence, GitHub), check `output/catalogs/` for
	metadata indexes with links back to the source of truth.

Do not guess about document content — read the actual files.
Do not read `src/` files unless the user is asking about pipeline code itself.

## Architecture Overview
The pipeline has 4 stages:
1. Harvest: collect staged local files and optional remote catalogs/content.
2. Translate: convert inputs into markdown with frontmatter.
3. Engine: detect changes, extract tickets, and build decision/changelog outputs.
4. Publish: assemble output docs and generate PROJECT_CONTEXT.md.

## Source of Truth
- Runtime behavior is config-driven via config/pipeline.yaml.
- Keep CLI behavior aligned with src/cli.py and src/pipeline.py.
- Preserve the curated staging model (no broad auto-ingestion).

## Contributor Guidance for Changes
- Favor deterministic, offline-friendly behavior.
- Keep output markdown Copilot-friendly and searchable.
- When changing stage behavior, update README and this file in the same change.
- Do not add AI/LLM service dependencies into pipeline logic.

## Stage-Specific Notes
### Harvest
- Local staging uses config/staging_manifest.json managed by CLI commands.
- Remote connectors are optional and enabled through config.

### Translate
- File-type routing is extension-based in src/translator/translator.py.
- Outputs should include stable metadata frontmatter.

### Engine
- Decision detection is keyword/rule based.
- Ticket extraction must remain configurable through regex patterns.

### Publish
- Maintain flat, predictable output structure under output/.
- PROJECT_CONTEXT.md should remain the main Copilot entry artifact.

## Environment and Execution
- Preferred local setup is python3 virtual environment in .venv.
- CLI usage should be validated with pm-pipeline --help.
- If credential files are used, ensure env values are available to the running process.
- Packaging backend in pyproject.toml should remain `setuptools.build_meta` to keep editable installs (`pip install -e .`) reliable.

## Documentation Consistency Rules
When behavior changes in these areas, update docs together:
1. CLI workflow changes: README and CONTRIBUTING.md.
2. Pipeline stage behavior: README and this file.
3. Env var names/usage: config/.env.example and README.
4. Chat skills/agent behavior: .github/skills/, .github/agents/, README, and this file.

## Skills and Agents Conventions
- Project skills live under `.github/skills/pm-doc-*/SKILL.md`.
- Project agents live under `.github/agents/*.agent.md`.
- Skills should reference project sources of truth (README.md, CONTRIBUTING.md, config/pipeline.yaml, this file).
- Use the `pm-doc-*` namespace for project-scoped skills to avoid collision with global skill sets.

## Token and Context Efficiency
- For project knowledge questions, always use `output/` artifacts. Never reconstruct
	answers from `src/` code when output artifacts are available.
- If a task does not require code edits, avoid reading `src/` files by default.
- Prefer generated artifacts first: `output/PROJECT_CONTEXT.md`, `output/DECISION_LOG.md`, and `output/CHANGELOG.md`.
- Read the smallest relevant file set and avoid loading large files when summaries are sufficient.
- For docs-only tasks, prioritize `README.md`, `CONTRIBUTING.md`, and `.github/` docs; inspect code only when needed for verification.
- For analysis-only requests, return recommendations without expanding code context unless the user requests deeper validation.

## Mermaid Diagram Style Standard
- Use a default Mermaid visual style for all new diagrams across this project unless the user explicitly requests a different style.
- Reuse the shared style snippet in templates/mermaid-style.md.
- Keep colors semantic and consistent:
	- Stage/process nodes: blue tones
	- Data/log/analysis nodes: green tones
	- Source/raw/input nodes: warm coral tones
	- Outcome/output nodes: bright blue tones
	- Human/user/actor nodes: warm yellow tones
- Prefer classDef-based styling over hardcoded one-off node styles.
- For new diagrams, include an init block with theme base and the shared themeVariables values.

Default behavior for Copilot:
- If a user asks for a Mermaid diagram and does not request a custom theme, apply the shared project style.
- If a user asks for another style, follow the user request and do not enforce the default palette.

## Common Questions Copilot Should Handle
These are the types of questions users will ask in this workspace:
- "What decisions were made about [topic]?" -> search DECISION_LOG.md and PROJECT_CONTEXT.md
- "What documents do we have about [topic]?" -> search PROJECT_CONTEXT.md document inventory
- "What tickets are referenced?" -> check PROJECT_CONTEXT.md ticket references section
- "Summarize [document name]" -> find and read the file under output/docs/
- "What changed recently?" -> read CHANGELOG.md
- "Give me a weekly summary" -> read or generate output/reports/WEEKLY_REPORT.md
- "Where is the doc about [topic] in Confluence/GitHub?" -> search output/catalogs/
