# Domino Governance Policy YAML Schema Reference

This reference documents the complete YAML structure for Domino Data Lab governance policies. Use it to generate valid policy YAML from unstructured documents.

## Top-Level Structure

A Domino policy YAML file has these top-level keys:

```yaml
enforceSequentialOrder: true|false    # Optional: gates stages sequentially
classification:                       # Optional: risk classification config
  rule: <string>                      # Classification logic (Go-like expression)
  artifacts:                          # List of aliased input artifact IDs
    - <alias-name>
stages:                               # Required: list of workflow stages
  - name: <stage-name>
    artifacts: [...]                  # Direct evidence in the stage
    approvers: [...]                  # Approver config
    evidence: [...]                   # Evidence for approvals
gates:                                # Optional: gating rules
  - name: <gate-name>
    rules: [...]
    approvals: [...]
approvers:                            # Optional: top-level approver defaults
  - name: <org-name>
    showByDefault: true|false
    editable: true|false
evidenceSet:                          # Optional: reusable evidence definitions
  - id: Local.<id>
    name: <display-name>
    description: <text>
    definition: [...]
```

## Stages

Stages organize the workflow. Each stage has a name, optional artifacts (evidence), and optional approvals.

```yaml
stages:
  - name: 'Stage 1: Initial Review'
  - name: 'Stage 2: Validation'
```

### Approvals Within Stages

Each approval has a name, approvers, and optional evidence:

```yaml
stages:
  - name: 'Stage 1: Review'
    approvers:
      - <org-name>
    evidence:
      id: Local.<evidence-id>
      name: <display-name>
      description: <text>
      definition:
        - artifactType: input
          details:
            label: "Question text?"
            type: radio
            options:
              - Yes
              - No
```

### Sequential Workflows

```yaml
enforceSequentialOrder: true
approvers:
  - name: <org-name>
    showByDefault: true
    editable: false
```

## Evidence and Evidence Sets

Evidence sets are reusable containers for inputs, checks, and guidance.

```yaml
evidenceSet:
  - id: Local.<set-id>
    name: <display-name>
    description: <text>
    definition:
      - artifactType: <type>
        details: { ... }
```

### Visibility on Evidence Sets

```yaml
evidenceSet:
  - id: Global.<id>
    visibility:
      conditions:
        - when: classification == "High"
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

```yaml
- artifactType: input
  details:
    type: select
    label: "Select the base model template."
    options:
      - label: "Template A"
        value: "templateA"
      - label: "Template B"
        value: "templateB"
```

### Multi-Select Dropdown

```yaml
- artifactType: input
  details:
    type: multiSelect
    label: "Select the data sets used."
    options:
      - label: "Data set 1"
        value: "dataset1"
      - label: "Data set 2"
        value: "dataset2"
```

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
    - <alias-name>

stages:
  - name: classificationExample
    artifacts:
      - id: Local.<artifact-id>
        name: <display-name>
        description: <text>
        definition:
          - artifactType: input
            aliasForClassification: <alias-name>
            details:
              label: "Risk rating?"
              type: radio
              options:
                - High
                - Low
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
