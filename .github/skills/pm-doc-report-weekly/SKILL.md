---
name: pm-doc-report-weekly
description: Generate a deterministic weekly markdown report from pipeline output artifacts.
argument-hint: "[--output output/reports/WEEKLY_REPORT.md]"
allowed-tools: Read, Write, Bash, Grep, Glob, AskUserQuestion
---

<objective>
Create a concise weekly report using existing generated artifacts, without AI-dependent transformations.
</objective>

<inputs>
- `--output output/reports/WEEKLY_REPORT.md` (optional): target file override.
- default mode: read existing output artifacts and generate markdown report only.
</inputs>

<execution_context>
@./.github/agents/pm-doc-pipeline-operator.agent.md
@./output/PROJECT_CONTEXT.md
@./output/DECISION_LOG.md
@./output/CHANGELOG.md
@./README.md
</execution_context>

<context>
$ARGUMENTS
</context>

<safety>
- Do not modify source artifacts in output/.
- Do not trigger pipeline reruns unless explicitly requested by user.
- Write only the report output file.
</safety>

<output_contract>
Generated markdown sections:
1. Summary
2. Decisions this period
3. Ticket impact
4. Change log highlights
5. Risks and follow-ups

Completion response sections:
1. Summary
2. Findings
3. Actions
4. Verification
</output_contract>

<verification_checklist>
- Required source artifacts are present.
- Output file created at expected path.
- Report includes required sections in fixed order.
- Counts in summary align with source artifact data.
</verification_checklist>

<process>
1. Validate source artifacts:
- output/PROJECT_CONTEXT.md
- output/DECISION_LOG.md
- output/CHANGELOG.md

2. Extract deterministic sections:
- Run metadata (documents, decisions, changes)
- Decision highlights
- Ticket references
- Recent changes

3. Generate markdown report at:
- default: output/reports/WEEKLY_REPORT.md
- override if --output is provided

4. Report structure:
- Summary
- Decisions this period
- Ticket impact
- Change log highlights
- Risks and follow-ups

5. Return completion output with generated file path and key counts.
</process>
