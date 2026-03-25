# Domino Governance Policy YAML Schema Reference

This reference documents the complete YAML structure for Domino Data Lab governance policies. Use it to generate valid policy YAML from unstructured documents.

## Top-Level Structure

A Domino policy YAML file has these top-level keys:

```yaml
enforceSequentialOrder: true|false    # Optional: gates stages sequentially
classification:                       # Optional: risk classification config
  rule: <string>                      # Classification logic (Go-like expression or named rule)
  artifacts:                          # List of aliased input artifact IDs used for classification
    - <alias-name>
stages:                               # Required: list of workflow stages
  - policyEntityId: <uuid>           # Required UUID for each stage
    name: <stage-name>
    evidenceSet:                      # Array of evidence containers for this stage
      - description: <text>
        definition: [...]             # Array of artifact definitions
        id: Local.<kebab-case>
        name: <display-name>
    approvals:                        # Array of approval definitions for this stage
      - policyEntityId: <uuid>
        name: <approval-name>
        approvers:
          - name: <org-name>
            showByDefault: true|false
            editable: true|false
        evidence:                     # Evidence collected as part of this approval
          id: Local.<kebab-case>
          name: <display-name>
          description: <text>
          definition: [...]
gates:                                # Optional: gating rules
  - name: <gate-name>
    rules: [...]
    approvals: [...]
```

## Stages

Each stage has a `policyEntityId`, a `name`, an `evidenceSet` array (the questions/inputs for that stage), and an `approvals` array.

```yaml
stages:
  - policyEntityId: a1b2c3d4-e5f6-7890-abcd-ef1234567890
    name: 'Stage 1: Initial Review'
    evidenceSet:
      - description: Describe what evidence is collected here
        definition:
          - policyEntityId: b2c3d4e5-f6a7-8901-bcde-f12345678901
            artifactType: input
            aliasForClassification: question-label-slug
            details:
              label: "Your question here?"
              type: radio
              options:
                - Yes
                - No
        id: Local.stage-1-evidence
        name: Stage 1 Evidence
    approvals:
      - policyEntityId: c3d4e5f6-a7b8-9012-cdef-123456789012
        name: 'Stage 1 Sign Off'
        approvers:
          - name: model-gov-org
            showByDefault: true
            editable: false
        evidence:
          id: Local.stage-1-signoff
          name: Stage 1 Approval
          description: Review and approve stage 1
          definition:
            - policyEntityId: d4e5f6a7-b8c9-0123-defa-234567890123
              artifactType: input
              details:
                label: "Do you approve this stage?"
                options:
                  - Approved
                  - Approved with Conditions
                  - Not Approved
                type: radio
```

> **Key structural rules:**
> - `evidenceSet` is nested **inside each stage** (not at the top level of the document)
> - `approvals` is an array of approval objects, each with its own `policyEntityId`, `name`, `approvers`, and `evidence`
> - `approvers` is nested inside each approval object (not at the stage level)

### Sequential Workflows

```yaml
enforceSequentialOrder: true
approvers:
  - name: <org-name>
    showByDefault: true
    editable: false
```

## Evidence Sets

Evidence sets are the containers for inputs, checks, and guidance within a stage. They are defined **inside each stage** under the `evidenceSet` key (not at the top level of the document).

```yaml
stages:
  - policyEntityId: <uuid>
    name: Stage Name
    evidenceSet:                   # ← nested inside the stage
      - description: <text>
        definition:
          - artifactType: <type>
            details: { ... }
        id: Local.<set-id>
        name: <display-name>
```

### Visibility on Evidence Sets

```yaml
stages:
  - name: Stage Name
    evidenceSet:
      - id: Local.<id>
        visibility:
          conditions:
            - when: classification == "High"
        definition: [...]
```

## Input Artifact Types

### Radio Buttons (single select)

```yaml
- artifactType: input
  details:
    type: radio
    label: "How would you rate the model risk?"
    options:
      - label: "High"
        value: "High"
      - label: "Medium"
        value: "Medium"
      - label: "Low"
        value: "Low"
    tooltip: "Guidance text"
```

Radio options can also be simple strings:
```yaml
    options:
      - Yes
      - No
```

### Text Input (single line)

```yaml
- artifactType: input
  details:
    type: textinput
    label: "What are the expected business benefits?"
    placeholder: "Explain the benefit"
    helpText: "Help text under the input"
```

### Text Area (multi-line)

```yaml
- artifactType: input
  details:
    type: textarea
    label: "Describe the model's intended use."
    height: 10
    placeholder: "Explain here"
    helpText: "Additional guidance"
```

### Select Dropdown (single select)

Options can be plain strings (preferred) or `{label, value}` objects:

```yaml
- artifactType: input
  details:
    type: select
    label: "Select the base model template."
    options:
      - "Template A"
      - "Template B"
```

### Multi-Select Dropdown

```yaml
- artifactType: input
  details:
    type: multiselect
    label: "Select the data sets used."
    options:
      - "Data set 1"
      - "Data set 2"
```

> **Important:** The type value is `multiselect` (all lowercase). The API rejects `multiSelect` (camelCase).

> **Options format:** Plain strings (`- "Value"`) work for all input types (radio, select, multiselect, checkbox). The `{label: "...", value: "..."}` object format also works but plain strings are simpler and preferred.

### Checkbox Group

```yaml
- artifactType: input
  details:
    type: checkbox
    label: "Select departments that will use the model."
    options:
      - label: "Sales"
        value: "DEPT001"
      - label: "Customer Success"
        value: "DEPT002"
```

### Date Input

```yaml
- artifactType: input
  details:
    type: date
    label: "What is the scheduled release date?"
    startDate: 20240612
    format: ISO8601
```

### Numeric Input

```yaml
- artifactType: input
  details:
    type: numeric
    label: "Allowed F-score for deployment?"
    min: 0
    max: 1
```

### File Upload

```yaml
- artifactType: metadata
  details:
    type: file
    label: "Model Validation Report"
    description: "Upload the model validation report. Max 500MB."
```

## Guidance Artifacts

### Text Block (Markdown)

```yaml
- artifactType: guidance
  details:
    type: textblock
    text: >-
      [Reference Link](https://example.com) Markdown-formatted guidance text
      explaining what the reviewer should consider.
```

### Text Banner (high-visibility)

```yaml
- artifactType: guidance
  details:
    type: banner
    text: >-
      Important: Review all documentation before proceeding.
```

## Metrics Checks

Automated checks against model metadata:

```yaml
metrics:
  - id: Local.<metric-id>
    name: <display-name>
    description: <text>
    definition:
      - artifactType: metadata
        details:
          type: modelmetric
          metrics:
            - name: Acc
              label: Accuracy
              aliases:
                - acc
                - Correct Classification Rate
              threshold:
                operator: '>='
                value: 0.8
```

## Scripted Checks

Custom validation logic executed as a job:

```yaml
- artifactType: policyScriptedCheck
  details:
    name: <check-name>
    label: <display-label>
    command: <script.py> <args> ${param_name}
    parameters:
      - name: <param_name>
        type: text
        default: <default-value>
    outputTypes:
      - txt
      - png
    environmentId: <env-id>
    hardwareTierId: <tier-id>
    volumeSizeGiB: 4
```

## Monitoring Checks

Connect to Domino Model Monitoring (DMM):

```yaml
- artifactType: policyMonitoringCheck
  details:
    name: <check-name>
    label: <display-label>
    alertTypes:
      - drift
      - data_quality
    actions:
      - type: notification
        recipients:
          - <org-name>
      - type: createFinding
        severity: high
        owner: <org-name>
```

## Classification

### Classification Inputs

Link an input to classification with `aliasForClassification`:

```yaml
classification:
  rule: <rule-expression>
  artifacts:
    - <alias-name>           # must match aliasForClassification on the input

stages:
  - policyEntityId: <uuid>
    name: classificationExample
    evidenceSet:             # ← use evidenceSet, not artifacts
      - description: <text>
        definition:
          - policyEntityId: <uuid>
            artifactType: input
            aliasForClassification: <alias-name>   # ← links to classification.artifacts
            details:
              label: "Risk rating?"
              type: radio
              options:
                - High
                - Low
        id: Local.<artifact-id>
        name: <display-name>
```

### Classification Rules

Simple rule returning a string label:

```yaml
classification:
  rule: |
    var ans string
    ans = "Low"
    if classificationInputs["model-risk"].(string) == "High" || classificationInputs["change-type"].(string) == "Major" {
      ans = "High"
    }
    return ans
```

### Visibility Rules

Show/hide sections based on classification or input values:

```yaml
evidenceSet:
  - id: Global.<id>
    visibility:
      conditions:
        - when: classification == "High"
```

## Gates

Gates block specific actions until approvals are granted:

```yaml
gates:
  - name: <gate-name>
    rules:
      - action: CreateApp|CreateEndpoint
        parameters:
          hardwareTierId:
            - <tier-id-1>
            - <tier-id-2>
          # OR use "any" to match all:
          # hardwareTierId: "any"
          # dataPlaneId: <plane-id>
    approvals:
      - <approval-stage-name>
```

Supported gate actions: `CreateApp`, `CreateEndpoint`
Supported gate parameters: `hardwareTierId`, `dataPlaneId`

## Important Notes

- Replace `user-organization-name` with your actual org name in approver fields.
- Environment IDs and Hardware Tier IDs are instance-specific — leave placeholders.
- Policies must be published before use and cannot be edited once published.
- Only Governance Administrators can create or edit policies.
- Classification rules use a Go-like expression syntax.
