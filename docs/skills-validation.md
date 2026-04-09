# Skills Validation Matrix

This document tracks validation for project-scoped Copilot skills under `.github/skills/pm-doc-*/SKILL.md`.

## Validation Modes

- Healthy state: environment and artifacts exist.
- Failure state: missing prerequisites or broken setup.

## Matrix

| Skill | Healthy Scenario | Failure Scenario | Expected Result | Status | Notes |
|---|---|---|---|---|---|
| `/pm-doc-doctor` | venv active, config valid, outputs present | missing config or missing staged source | PASS/WARN/FAIL with remediation | TODO | includes --fix mode for install repair |
| `/pm-doc-state-audit` | consistent staging/raw/processed | stale staging manifest entries | severity-grouped findings + actions | TODO | |
| `/pm-doc-report-weekly` | output artifacts available, runs pm-pipeline report | missing PROJECT_CONTEXT.md | deterministic report or clear blocker | TODO | backed by src/engine/report.py |

## Acceptance Gates

1. Discoverability: all `/pm-doc-*` skills invokable in repository chat context.
2. Safety: destructive actions require explicit flags or confirmations.
3. Determinism: repeated runs with same input produce same report/check shape.
4. Documentation: README and CONTRIBUTING examples match skill behavior.

## Evidence Capture

For each skill run, capture:
- invocation command
- key output excerpt
- generated artifact path(s)
- pass/fail decision
- remediation follow-up (if needed)
