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

2. Run `pm-pipeline report` to generate the deterministic report.
3. Read the generated output/reports/WEEKLY_REPORT.md.
4. Present the report content to the user.
5. If the user asks for interpretation or follow-ups, provide analysis based on the generated report.
</process>
