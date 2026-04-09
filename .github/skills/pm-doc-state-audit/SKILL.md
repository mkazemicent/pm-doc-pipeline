---
name: pm-doc-state-audit
description: Audit staging, raw, processed, and output consistency and provide corrective actions.
argument-hint: "[--fix-suggestions]"
allowed-tools: Read, Bash, Grep, Glob
---

<objective>
Audit repository data state to detect inconsistencies before or after pipeline runs.
</objective>

<inputs>
- `--fix-suggestions` (optional): include prioritized remediation commands.
- default mode: diagnostics and findings only.
</inputs>

<execution_context>
@./.github/agents/pm-doc-pipeline-operator.agent.md
@./config/pipeline.yaml
@./README.md
</execution_context>

<context>
$ARGUMENTS
</context>

<safety>
- This skill is read-only.
- Do not modify manifests or delete files.
- Provide suggested commands for user approval instead of direct mutation.
</safety>

<output_contract>
1. Summary
2. Findings (blocking/warn/info)
3. Actions
4. Verification
</output_contract>

<verification_checklist>
- Staging manifest existence and staged source path health checked.
- raw/processed/output counts checked.
- output core artifacts checked.
- Corrective actions included for all blocking findings.
</verification_checklist>

<process>
1. Inspect staging manifest:
- Check whether config/staging_manifest.json exists.
- Validate each staged source path exists.

2. Inspect raw/processed/output alignment:
- Count files per area.
- Detect likely orphaned processed files with no corresponding raw source signal.

3. Inspect critical outputs:
- Ensure output/PROJECT_CONTEXT.md, output/DECISION_LOG.md, output/CHANGELOG.md existence.

4. Return findings grouped by severity:
- blocking issues
- warnings
- informational notes

5. Provide corrective command suggestions for each issue.
</process>
