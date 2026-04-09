---
name: pm-doc-doctor
description: Diagnose local setup and pipeline readiness with actionable PASS/WARN/FAIL checks.
argument-hint: "[--verbose] [--json] [--fix]"
allowed-tools: Read, Bash, Grep, Glob, AskUserQuestion
---

<objective>
Run a deterministic health audit for pm-doc-pipeline and return clear next actions.

Checks should cover:
- Environment and executable readiness
- Config validity
- Directory and artifact health
- Staging integrity
- Remote credential readiness when sources are enabled
</objective>

<inputs>
- `--verbose` (optional): include command output details.
- `--json` (optional): return machine-readable check results.
- `--fix` (optional): apply safe repair commands (upgrade pip/setuptools, reinstall editable package, refresh shell cache). Without this flag, only diagnostics are returned.
- default mode: human-readable summary.
</inputs>

<execution_context>
@./.github/agents/pm-doc-pipeline-operator.agent.md
@./.github/copilot-instructions.md
@./README.md
@./CONTRIBUTING.md
@./config/pipeline.yaml
</execution_context>

<context>
$ARGUMENTS
</context>

<safety>
- Default mode is read-only and non-destructive.
- Do not modify files.
- Repair commands only run when --fix is explicitly provided.
- If fix actions are needed, provide commands for user confirmation.
</safety>

<output_contract>
Human mode sections:
1. Summary
2. Findings (PASS/WARN/FAIL)
3. Actions
4. Verification

JSON mode object:
{
	"status": "pass|warn|fail",
	"checks": [{"name": "...", "severity": "pass|warn|fail", "evidence": "...", "remediation": "..."}],
	"actions": ["..."],
	"verification": ["..."]
}
</output_contract>

<verification_checklist>
- CLI availability verified with `pm-pipeline --help`.
- Config file parsed successfully.
- raw/processed/output state checked.
- Staged file existence checked when manifest exists.
- Remote env prerequisites checked only for enabled sources.
</verification_checklist>

<process>
1. Validate CLI and runtime basics:
- Check python3, virtual environment hint, and `pm-pipeline --help`.

2. Validate configuration:
- Ensure config file exists and can be parsed.
- Confirm required top-level sections (general, sources, translator, engine, publisher).

3. Validate repository runtime state:
- Check raw/, processed/, output/ folder existence and basic file counts.
- Check whether output/PROJECT_CONTEXT.md exists.

4. Validate staging integrity:
- If config/staging_manifest.json exists, verify each staged source path exists.
- Report missing staged files separately.

5. Validate remote source prerequisites:
- For any enabled remote source in config, check corresponding environment variables are available.

6. Return a summary:
- PASS: usable now.
- WARN: usable with caveats.
- FAIL: blocked, include exact fix commands.

7. If --fix is requested:
	a) Run: python3 -m pip install --upgrade pip setuptools wheel
	b) Run: python3 -m pip install -e .
	c) Run: hash -r
	d) Verify: pm-pipeline --help
	e) Return fixed / partially fixed / blocked with evidence.

8. If --json is requested, provide structured JSON output with checks, severity, evidence, and remediation fields.
</process>
