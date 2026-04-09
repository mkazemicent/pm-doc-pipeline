---
name: pm-doc-install-fix
description: Troubleshoot and fix local install issues such as editable install failures and missing CLI command.
argument-hint: "[--check] [--apply]"
allowed-tools: Read, Bash, Grep, AskUserQuestion
---

<objective>
Resolve common installation and invocation failures without destructive changes.

Primary targets:
- editable install errors
- missing pm-pipeline command
- packaging backend mismatch
- stale shell command cache
</objective>

<inputs>
- `--check` (optional): diagnostics only, no changes.
- `--apply` (optional): apply safe repair commands.
- default mode: `--check` behavior.
</inputs>

<execution_context>
@./.github/agents/pm-doc-pipeline-operator.agent.md
@./pyproject.toml
@./README.md
@./CONTRIBUTING.md
</execution_context>

<context>
$ARGUMENTS
</context>

<safety>
- Default is non-mutating diagnostics.
- Only run repair commands when `--apply` is explicitly requested.
- Never delete repository content or reset git state.
</safety>

<output_contract>
1. Summary
2. Findings
3. Actions (commands run or proposed)
4. Verification
</output_contract>

<verification_checklist>
- build-backend is `setuptools.build_meta`.
- editable install can complete.
- command resolution works for both `pm-pipeline --help` and `python3 -m src.cli --help`.
</verification_checklist>

<process>
1. Run diagnostics:
- Verify active python3 and pip versions.
- Verify `build-backend` in pyproject.toml is `setuptools.build_meta`.
- Verify editable install state and `pm-pipeline --help`.

2. If --check mode (or no mode provided):
- Return issue list and exact remediation commands only.

3. If --apply mode:
- Apply safe fixes in order:
  a) upgrade pip/setuptools/wheel
  b) reinstall editable package (`python3 -m pip install -e .`)
  c) refresh shell cache (`hash -r`)
  d) verify both `pm-pipeline --help` and `python3 -m src.cli --help`

4. Return final result:
- fixed / partially fixed / blocked
- include exact remaining blocker if blocked.
</process>
