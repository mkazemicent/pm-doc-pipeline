---
name: pm-doc-test-scenario
description: Run a deterministic local test scenario that validates all pipeline stages and output artifacts.
argument-hint: "[--preserve-inputs] [--cleanup]"
allowed-tools: Read, Bash, Write, Grep, Glob, AskUserQuestion
---

<objective>
Execute an end-to-end local scenario that proves harvest, translate, engine, and publish are functioning.
</objective>

<inputs>
- `--preserve-inputs` (optional): keep generated sample input files.
- `--cleanup` (optional): remove staged entries and generated sample files.
- default mode: remove staged entries, keep generated sample inputs.
</inputs>

<execution_context>
@./.github/agents/pm-doc-pipeline-operator.agent.md
@./README.md
@./config/pipeline.yaml
</execution_context>

<context>
$ARGUMENTS
</context>

<safety>
- Create sample inputs only in a dedicated temporary test folder.
- Do not remove user files outside generated test inputs.
- Cleanup that removes files requires explicit `--cleanup`.
</safety>

<output_contract>
1. Summary
2. Findings
3. Actions
4. Verification
</output_contract>

<verification_checklist>
- `pm-pipeline run` completes without stage errors.
- output/PROJECT_CONTEXT.md, output/DECISION_LOG.md, output/CHANGELOG.md exist.
- Decision and ticket extraction present for seeded test content.
- Cleanup behavior follows mode flags.
</verification_checklist>

<process>
1. Create controlled sample inputs (markdown, txt, html) in a temporary local folder.
2. Stage sample files with `pm-pipeline add`.
3. Run `pm-pipeline run` and `pm-pipeline status`.
4. Validate outputs exist:
- output/PROJECT_CONTEXT.md
- output/DECISION_LOG.md
- output/CHANGELOG.md
- output/docs/*

5. Validate extraction behavior:
- Confirm at least one decision was detected.
- Confirm ticket references appear when test content includes them.

6. Return pass/fail summary with evidence snippets.

7. Cleanup behavior:
- Default: remove staged sample entries.
- If --preserve-inputs is supplied, keep sample source files.
- If --cleanup is supplied, remove both staged entries and sample files.
</process>
