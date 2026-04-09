# Copilot Instructions for PM Doc Pipeline

## Project Intent
This project builds a curated, local-first PM knowledge base that Copilot can query reliably.
Prioritize high-signal outputs over broad ingestion.

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
