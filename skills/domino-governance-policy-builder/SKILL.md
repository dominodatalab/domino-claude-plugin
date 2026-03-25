---
name: domino-policy-generator
description: >
  Convert unstructured policy documents (PDFs, Word docs, plain text, Markdown) into valid Domino
  Data Lab governance policy YAML. Use this skill whenever someone asks to create, generate, build,
  or draft a Domino governance policy from a document, regulation, compliance framework, risk
  management standard, or any written policy description. Also trigger when someone uploads a file
  and asks to turn it into a Domino policy, or says things like "convert this to a governance policy",
  "create policy YAML from this", "build a Domino policy for model risk", or "generate a governance
  workflow from this document". Even if the user just says "make this a policy" with an uploaded file,
  use this skill. This skill covers the full Domino policy YAML schema including stages, approvals,
  evidence, inputs, classification, visibility rules, gates, metrics checks, scripted checks, and
  monitoring checks.
---

# Domino Policy Generator

Convert unstructured policy documents into valid Domino Data Lab governance policy YAML.

## When This Skill Activates

This skill should be used when:
- A user uploads a PDF, DOCX, TXT, or MD file describing a policy, regulation, or compliance framework and wants it turned into a Domino governance policy
- A user describes a governance workflow in conversation and wants it encoded as Domino policy YAML
- A user asks to create, draft, or generate a Domino governance policy from any source material

## Step 1: Read the Input Document

Before doing anything, read the uploaded document to understand its contents.

- **If the document content is already visible in context** (e.g., pasted text, Markdown, or a PDF/image rendered in context), — skip file reading and work directly from what you see.
- **If the file is on disk but not in context**, read it:
  - For PDFs: use the `pdf-reading` skill at `/mnt/skills/public/pdf-reading/SKILL.md`
  - For DOCX: use the `docx` skill at `/mnt/skills/public/docx/SKILL.md` (or use `python-docx` to extract text)
  - For plain text / Markdown: read directly with the `view` tool or `cat`

**Goal**: Extract the full text content so you can analyze its structure.

## Step 2: Load the Schema Reference and Example Policies

Read ALL reference files before generating any YAML:

```
view /mnt/skills/user/domino-policy-generator/references/domino-policy-schema.md
view /mnt/skills/user/domino-policy-generator/references/example-eu-ai-act-policy.md
view /mnt/skills/user/domino-policy-generator/references/example-oil-gas-policy.md
```

The **schema reference** documents every valid YAML construct. The **example policies** show
two real production policies with annotated structural patterns:

- **EU AI Act example** — Complex regulatory framework with 8 stages, classification rules,
  conditionalDisplay, structured checklists, gates, and a final executive consolidation stage.
  Use this pattern for complex regulatory/compliance frameworks.

- **Oil & Gas example** — Simpler operational workflow with 4 stages, textarea-heavy evidence,
  multiple approver groups, no classification block, no conditionalDisplay, no gates.
  Use this pattern for industry-specific operational governance.

**Choose the pattern that best fits the source document's complexity.** Both are valid.
Do not invent YAML keys or structures not in the references.

## Step 3: Analyze the Source Document

Read through the extracted text and identify these elements:

1. **Workflow stages** — Are there distinct phases of review? (e.g., "initial assessment", "validation", "final approval") These become `stages`.

2. **Approval requirements** — Who needs to approve? Are there specific roles, teams, or organizations? These become `approvers` within stages. Use placeholder org names like `your-org-name` if the document doesn't specify Domino org names.

3. **Evidence / questions** — What information must be collected? Look for:
   - Yes/No questions → `radio` inputs
   - Short text answers → `textinput`
   - Long text answers → `textarea`
   - Pick-one-from-list → `select`
   - Pick-many-from-list → `multiselect` or `checkbox`
   - Date fields → `date`
   - Numeric thresholds → `numeric`
   - Document uploads required → `file` (under `metadata` artifactType)

4. **Risk classification** — Does the document define risk tiers (e.g., High/Medium/Low)? If so, create a `classification` block with:
   - Input artifacts linked via `aliasForClassification`
   - A `rule` expression that maps inputs to a tier label

5. **Conditional logic** — Are some requirements only relevant for certain risk levels or answers? These become `visibility` rules on evidence sets.

6. **Gating requirements** — Does the document restrict deployments or actions until approvals are complete? These become `gates` with actions like `CreateApp` or `CreateEndpoint`.

7. **Automated checks** — Does the document require model performance thresholds? These become `metrics` checks. Does it require custom validation scripts? These become `policyScriptedCheck` artifacts. Does it reference monitoring for drift/data quality? These become `policyMonitoringCheck` artifacts.

8. **Guidance / instructions** — Informational text that should appear to reviewers. These become `guidance` artifacts (`textblock` or `banner`).

9. **Sequential ordering** — Must stages be completed in order? If so, set `enforceSequentialOrder: true`.

### Choosing the Right Complexity Level

Based on your analysis, decide which example pattern to follow:

**Use the complex pattern (EU AI Act style) when:**
- The source is a formal regulatory framework with many enumerable requirements
- Multiple risk tiers drive different requirements (need classification + conditionalDisplay)
- Structured checklists and multi-select options are natural fits
- A final executive consolidation stage is appropriate
- Gates are needed to block deployment actions

**Use the simpler pattern (Oil & Gas style) when:**
- The source describes a linear operational workflow
- Requirements are mostly open-ended narratives (textarea-heavy)
- Approvals are straightforward Yes/No decisions
- Different teams approve different stages (multiple approver groups)
- No complex conditional logic is needed
- No executive consolidation stage is required

**You can also mix patterns** — for example, use structured checklists in early stages and
textarea-heavy evidence in later stages, depending on what the source document calls for.

## Step 4: Generate the Policy YAML

Now construct the YAML. Follow these principles closely — they are derived from both the
schema documentation and the production EU AI Act example policy.

### Generate UUIDs
Every `policyEntityId` must be a unique UUID v4. Generate them with Python:
```python
import uuid
str(uuid.uuid4())
```
Place `policyEntityId` as the **first key** in every stage, approval, and individual artifact
definition. Note: `evidenceSet` container items do **not** need a `policyEntityId`.

### Structure
- Start with top-level `classification` (if needed), then `stages`
- Each stage contains an `evidenceSet` array (NOT flat `evidence`)
- Each evidence set item has: `description`, `definition` (array of artifacts), `id`, `name`
- Approvals are nested within each stage with their own `evidence` block
- Gates go at the top level after stages

### aliasForClassification on Every Input
Following the production example, add `aliasForClassification` to EVERY input artifact,
not just classification inputs. Use a kebab-case slug of the label text:
```yaml
aliasForClassification: select-all-applicable-risk-categories
```

### conditionalDisplay for Dynamic Fields
Use `conditionalDisplay` on individual artifacts to show/hide based on another input:
```yaml
details:
  conditionalDisplay:
    dependsOn: Local.<evidence-set-id>
    showIfValue: "Some Option"
  label: "Follow-up question..."
```

### Naming Conventions
- Stage names: Descriptive without number prefixes (e.g., "AI System Classification and Risk Assessment")
- Evidence IDs: `Local.<kebab-case>` (e.g., `Local.model-risk-assessment`)
- Approval names: End with "Sign Off" (e.g., "Risk Assessment Sign Off")
- Approver orgs: Use placeholder `model-gov-org` with `showByDefault: true` and `editable: false`

### Approval Evidence Pattern
Every stage approval should follow one of these patterns:

**Formal pattern** (for regulatory/compliance policies):
```yaml
approvals:
  - policyEntityId: <uuid>
    name: "<Stage Topic> Sign Off"
    approvers:
      - name: model-gov-org  # Replace with your organization name
        showByDefault: true
        editable: false
    evidence:
      id: Local.<stage>-signoff
      name: "<Stage Topic> Approval"
      description: "Review and approve..."
      definition:
        - policyEntityId: <uuid>
          artifactType: input
          details:
            label: "Do you approve...?"
            options:
              - Approved
              - Approved with Conditions
              - Not Approved
            type: radio
```

**Simple pattern** (for operational workflows):
```yaml
approvals:
  - policyEntityId: <uuid>
    name: "<Stage Topic> Approval"
    approvers:
      - name: modeling-leadership
        showByDefault: true
        editable: false
      - name: modeling-review    # Multiple approver groups are supported
        showByDefault: true
        editable: false
    evidence:
      id: Local.<stage>-signoff
      name: "<Stage Topic> Signoff"
      description: "Review and approve..."
      definition:
        - policyEntityId: <uuid>
          artifactType: input
          details:
            label: "Have you reviewed and approved...?"
            options:
              - "Yes"
              - "No"
            type: radio
```

Use multiple approver groups when different teams are responsible for different stages.

### Final Executive Stage
Include a final stage that consolidates all prior stage statuses. This stage:
- Re-collects status of each prior stage (Approved/Approved with Conditions/Not Approved/Pending)
- Includes an executive summary textarea
- Has executive management sign-off
- Optionally has board-level sign-off (conditionally displayed for high-risk items)

### Textarea Placeholders
Always provide concrete placeholder text guiding what the reviewer should write.

### Completeness
- Map every requirement from the source document to a YAML construct
- If something doesn't map cleanly to a Domino construct, add it as a `guidance` textblock
- Include `tooltip` or `helpText` where the source provides explanatory context

### Placeholders for Instance-Specific Values
- Environment IDs: use `[your-environment-id]`
- Hardware tier IDs: use `small-k8s` as default
- Organization names: use `model-gov-org` (the convention from the example)

## Step 5: Add a Mapping Summary

After the YAML, provide a brief summary that maps source document sections to the generated YAML components. This helps the user verify coverage and understand the translation. Format it as a table or short list:

| Source Document Section | YAML Component |
|---|---|
| Section 2.1: Risk Assessment | Stage 1 + classification block |
| Section 3: Model Validation | Stage 2 approval evidence |
| ... | ... |

Also call out:
- Anything in the source document that couldn't be mapped to Domino YAML (explain why)
- Anything that needs manual configuration (org names, environment IDs, hardware tier IDs)
- Suggested improvements or optional enhancements (e.g., "You could add a gate to block deployments until Stage 2 is approved")

## Step 6: Output the YAML File

Save the generated policy YAML to a file for the user to download:

```bash
# Save to outputs so the user can download it
cp /home/claude/policy.yaml /mnt/user-data/outputs/domino-policy.yaml
```

Use `present_files` to share the file with the user.

## Quality Checklist

Before presenting the output, verify:

- [ ] All YAML is valid (proper indentation, no syntax errors — validate with `yaml.safe_load()`)
- [ ] Every stage, approval, and artifact has a unique `policyEntityId` (UUID v4); evidenceSet container items do NOT need one
- [ ] Every `artifactType` is one of: `input`, `metadata`, `guidance`, `policyScriptedCheck`, `policyMonitoringCheck`
- [ ] Every input `type` is one of: `radio`, `textinput`, `textarea`, `select`, `multiselect`, `checkbox`, `date`, `numeric` (all lowercase — `multiselect` not `multiSelect`)
- [ ] Every input artifact has an `aliasForClassification` (kebab-case slug of the label)
- [ ] Every `id` follows the `Local.<kebab-case>` pattern
- [ ] Every stage has an `evidenceSet` array (not flat `evidence`)
- [ ] Every stage has an `approvals` block with a "Sign Off" approval following the standard pattern
- [ ] A final executive/summary stage consolidates prior stage statuses
- [ ] `conditionalDisplay` is used for fields that depend on other answers
- [ ] Classification rules use the Go-like expression syntax (or a named rule reference)
- [ ] Gate actions are one of: `CreateApp`, `CreateEndpoint`
- [ ] Approver org names use `model-gov-org` as placeholder with `showByDefault: true, editable: false`
- [ ] Environment/hardware tier IDs have placeholder values
- [ ] Textarea inputs have descriptive `placeholder` text
- [ ] The YAML can be pasted directly into Domino's Code editor

## Tips for Ambiguous Source Material

Policy documents are often vague. When you encounter ambiguity:

- **No clear stages?** Default to a two-stage workflow: "Assessment" and "Approval"
- **No specific approvers?** Use a generic `your-org-name` approver
- **Vague requirements like "ensure model quality"?** Create a textarea asking the reviewer to describe how quality was validated, plus a guidance textblock with the original requirement text
- **Regulatory references?** Include them as `guidance` textblocks with links if URLs are present
- **Complex conditional logic?** Start with simple visibility rules; add a comment suggesting the user may want to refine the classification rule
- **Performance thresholds mentioned but not specific?** Create a numeric input asking for the threshold, rather than hardcoding a metrics check

## Example: Minimal Policy (Production Pattern)

Here's the simplest valid policy following the production conventions:

```yaml
classification:
  rule: RISK-ASSESSMENT
  artifacts:
    - risk-level
stages:
  - policyEntityId: a1b2c3d4-e5f6-7890-abcd-ef1234567890
    name: Risk Assessment
    evidenceSet:
      - description: Assess the risk level of the system
        definition:
          - policyEntityId: b2c3d4e5-f6a7-8901-bcde-f12345678901
            artifactType: input
            aliasForClassification: what-is-the-risk-level
            details:
              label: What is the risk level?
              options:
                - High
                - Medium
                - Low
              type: radio
        id: Local.risk-assessment
        name: Risk Assessment
    approvals:
      - policyEntityId: c3d4e5f6-a7b8-9012-cdef-123456789012
        name: Risk Assessment Sign Off
        approvers:
          - name: model-gov-org
            showByDefault: true
            editable: false
        evidence:
          description: Review and approve the risk assessment
          definition:
            - policyEntityId: d4e5f6a7-b8c9-0123-defa-234567890123
              artifactType: input
              details:
                label: Do you approve the risk assessment?
                options:
                  - Approved
                  - Approved with Conditions
                  - Not Approved
                type: radio
          id: Local.risk-assessment-signoff
          name: Risk Assessment Approval
```
