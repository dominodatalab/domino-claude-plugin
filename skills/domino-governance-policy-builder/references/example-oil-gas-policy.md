# Example Domino Governance Policy: Oil & Gas Predictive Model Governance

This is a production policy for AI/ML predictive model governance in the Oil & Gas industry.
It demonstrates a simpler, more streamlined structure compared to the EU AI Act example.
Use both examples together to understand the range of valid patterns.

## Key Differences from the EU AI Act Example

### 1. No Classification Block
This policy has no top-level `classification` section. Not all policies need risk classification
— simpler workflows can skip it entirely. The risk level is still captured via a radio input
within the evidence set, but it's not wired to a classification rule.

### 2. Simpler Approval Patterns
Instead of "Approved / Approved with Conditions / Not Approved", this policy uses
simple "Yes" / "No" radio buttons for approval sign-off questions. Both patterns are valid.
The simpler pattern works well for operational workflows.

### 3. Multiple Approver Groups
This policy assigns **different approver groups** to different stages:
- Stage 1: `modeling-leadership` only
- Stage 2: `modeling-practitioners` + `modeling-leadership`
- Stage 3: `modeling-review` + `modeling-practitioners`
- Stage 4: `modeling-leadership` + `modeling-review`

This demonstrates that approvers can vary by stage and multiple groups can be assigned.

### 4. Guidance Artifacts with Regulatory Links
The first stage starts with a `guidance` textblock that provides regulatory context and links:
```yaml
- artifactType: guidance
  details:
    text: >-
      This stage involves defining the operational problem... This includes
      ensuring compliance with EPA, OSHA, PHMSA, and BSEE regulations where
      applicable. [Learn More](https://www.bsee.gov/oil-gas)
```
This is a good pattern for embedding regulatory references directly in the policy.

### 5. Radio Options as Simple Strings vs Label/Value Objects
This policy mixes both styles:
```yaml
# Simple strings (most of the policy):
options:
  - "Yes"
  - "No"

# Label/value objects (in validation stage):
options:
  - label: "Yes"
    value: "Yes"
  - label: "No"
    value: "No"
```
Both are valid. Use simple strings when the display text and value are the same.

### 6. Textarea-Heavy Evidence Collection
Most evidence in this policy is collected via `textarea` inputs with detailed, domain-specific
prompts — not structured dropdowns or checkboxes. This works well when the source
document describes open-ended requirements rather than enumerable options.

### 7. No `conditionalDisplay`
This simpler policy doesn't use conditional display logic. Not every policy needs it.

### 8. Scripted Checks and Metrics in Validation Stage
The validation stage combines multiple artifact types in a single evidence set:
- `metadata` with `type: modelmetric` (automated metric thresholds for RMSE and R²)
- `policyScriptedCheck` (data quality validation script)
- `metadata` with `type: file` (manual report upload)

This is a powerful pattern for combining automated and manual validation.

### 9. No Final Executive Stage
Unlike the EU AI Act example, this policy does NOT have a final consolidation stage.
The last stage is the deployment authorization itself. A final executive stage is optional
and mainly useful for complex regulatory frameworks.

### 10. No Gates
This policy doesn't use gates. Gates are optional and mainly useful when you need to
block specific Domino actions (CreateApp, CreateEndpoint) until approvals complete.

## When to Use This Pattern vs the EU AI Act Pattern

Use the **simpler O&G pattern** when:
- The source document describes a linear operational workflow
- Risk classification is informal or single-question
- Approvals are straightforward Yes/No decisions
- Most evidence is open-ended narrative rather than structured checklists
- No complex conditional logic is needed
- No regulatory requirement for executive/board consolidation

Use the **EU AI Act pattern** when:
- The source document is a complex regulatory framework
- Multiple risk tiers drive different requirements
- Conditional display is needed for dynamic forms
- A final executive consolidation stage is required
- Structured checklists and enumerations are prominent
- Gates are needed to block deployment actions

## Structural Summary

This policy contains **4 stages**:

1. **Problem Definition and Risk Assessment** — guidance textblock with regulatory links,
   operational problem definition (textarea), risk level (radio: High/Medium/Low),
   data sources (textarea), success metrics (textarea). Approved by `modeling-leadership`.

2. **Model Design and Development** — model architecture (textarea), limitations (textarea),
   implementation details (textarea), development results (textarea).
   Approved by `modeling-practitioners` + `modeling-leadership`.

3. **Model Validation** — methodology validation (textarea + radios), model quality metrics
   (automated RMSE/R² thresholds + scripted data quality check + file upload),
   operational readiness (textarea).
   Approved by `modeling-review` + `modeling-practitioners`.

4. **Deployment Authorization and Monitoring** — deployment strategy (textarea),
   scalability/resilience (textarea), security/compliance (textarea),
   continuous monitoring framework (textarea).
   Approved by `modeling-leadership` + `modeling-review`.

## Full Example YAML

```yaml
stages:
    - policyEntityId: f90cc6c9-11c0-4071-bffa-ed721a2c5740
      name: Problem Definition and Risk Assessment
      approvals:
        - policyEntityId: 2cc8c56b-104d-43fe-a569-4397f838a18f
          name: Problem Definition and Risk Approval
          approvers:
            - editable: false
              name: modeling-leadership
              showByDefault: true
          evidence:
            id: Local.problem-definition-signoff
            name: Problem Definition Approval
            description: Review and approve problem definition and risk assessment
            definition:
                - policyEntityId: a3ddf7bf-3e16-4417-864c-458149267cd4
                  artifactType: input
                  details:
                    label: Have you reviewed the operational problem definition and validated alignment with O&G industry standards and regulations?
                    options:
                        - "Yes"
                        - "No"
                    type: radio
                - policyEntityId: e866e55e-8b11-4b29-b001-4c2b65b2eb0a
                  artifactType: input
                  details:
                    label: Do you authorize the project to proceed to the design and development phase?
                    options:
                        - "Yes"
                        - "No"
                    type: radio
      evidenceSet:
        - id: Local.og-industry-guidance
          name: Oil and Gas Regulatory Guidance
          description: Oil and Gas industry guidance for AI/ML model governance
          definition:
            - policyEntityId: 046e9aaa-23fe-4ed3-b0e9-a67e75264053
              artifactType: guidance
              details:
                text: This stage involves defining the operational problem and conducting initial risk assessment aligned with Oil and Gas industry regulations and best practices. All predictive models must integrate environmental, safety, and operational risk considerations from the planning phase through deployment. This includes ensuring compliance with EPA, OSHA, PHMSA, and BSEE regulations where applicable. [Learn More](https://www.bsee.gov/oil-gas)
        - id: Local.operational-problem
          name: Operational Problem Definition
          description: Defines operational problem and predictive model purpose
          definition:
            - policyEntityId: cf3cfe7f-5d15-4daf-93f7-f4aaec842ffb
              artifactType: input
              aliasForClassification: operational-problem-definition
              details:
                label: Provide a detailed description of the operational problem, predictive model purpose, and business requirements. Include justification for ML/AI use over alternative solutions (e.g., equipment failure prediction, production optimization, pipeline integrity monitoring).
                type: textarea
        - id: Local.comprehensive-risk-assessment
          name: Comprehensive Risk Assessment
          description: Conduct comprehensive risk and regulatory assessment
          definition:
            - policyEntityId: f0a24185-253a-4d0b-853b-cbdf3be5bd06
              artifactType: input
              aliasForClassification: model-risk
              details:
                label: Document risk assessment findings including operational, environmental, safety, and regulatory considerations. Classify overall risk level based on potential impact.
                options:
                    - High
                    - Medium
                    - Low
                type: radio
        - id: Local.validated-data-sources
          name: Validated Data Sources
          description: List and validate data sources for compliance
          definition:
            - policyEntityId: 60c7cbfe-e382-4049-8c1a-4c85e278618b
              artifactType: input
              aliasForClassification: validated-data-sources
              details:
                label: Provide comprehensive list of all data sources including sensor data, operational logs, maintenance records, and production data. Validate data quality, provenance, and compliance with data governance requirements.
                type: textarea
        - id: Local.operational-metrics
          name: Operational Success Metrics
          description: Define operational success metrics and performance requirements
          definition:
            - policyEntityId: 028366fd-6e0b-4607-a19d-a22bc64f41a7
              artifactType: input
              aliasForClassification: operational-metrics
              details:
                label: Specify operational success metrics, performance requirements, and operational thresholds. Include accuracy, reliability, and safety-related measures relevant to the use case.
                type: textarea
    - policyEntityId: dc7c2ad8-bd43-4805-b50a-b8ff7aeaff33
      name: Model Design and Development
      approvals:
        - policyEntityId: efba8ba4-8e3f-4747-a875-04b51ccfceed
          name: Model Design Approval
          approvers:
            - editable: false
              name: modeling-practitioners
              showByDefault: true
            - editable: false
              name: modeling-leadership
              showByDefault: true
          evidence:
            id: Local.design-approval-signoff
            name: Model Design Signoff
            description: Review and approve model design and development
            definition:
                - policyEntityId: b50e4856-7944-4154-b975-09684af90d85
                  artifactType: input
                  details:
                    label: Have you reviewed the predictive model design and validated implementation practices?
                    options:
                        - "Yes"
                        - "No"
                    type: radio
                - policyEntityId: d4df4bec-a509-4ec2-bec9-756cad35d28f
                  artifactType: input
                  details:
                    label: Do you approve the model design for validation testing?
                    options:
                        - "Yes"
                        - "No"
                    type: radio
      evidenceSet:
        - id: Local.model-architecture
          name: Predictive Model Architecture
          description: Document predictive model architecture and approach
          definition:
            - policyEntityId: d1c6a72a-7b80-452d-92a6-842a89aedfe9
              artifactType: input
              aliasForClassification: model-architecture
              details:
                label: Describe the chosen predictive model architecture, algorithms, and design decisions. Include justification for selections based on operational requirements (e.g., regression models for equipment RUL prediction, time series forecasting for production optimization).
                type: textarea
        - id: Local.model-limitations
          name: Model Limitations and Constraints
          description: Document model limitations and operational constraints
          definition:
            - policyEntityId: 3fc85434-5e2b-4bab-99ea-85e43ed5a485
              artifactType: input
              aliasForClassification: model-limitations
              details:
                label: List known limitations, constraints, and potential failure modes of the predictive model. Include data quality considerations, sensor reliability assumptions, and operational boundary conditions.
                type: textarea
        - id: Local.implementation-details
          name: Model Implementation Details
          description: Implement predictive model with industry best practices
          definition:
            - policyEntityId: a889bbd1-3237-4428-b7e2-d69da3ecbe08
              artifactType: input
              aliasForClassification: implementation-details
              details:
                label: Provide implementation details demonstrating incorporation of industry best practices including feature engineering approach, handling of missing sensor data, and model interpretability mechanisms.
                type: textarea
        - id: Local.development-results
          name: Development Results and Analysis
          description: Document development results and performance analysis
          definition:
            - policyEntityId: 4350e951-b829-4a2c-8817-d1b6f8405fbd
              artifactType: input
              aliasForClassification: development-results
              details:
                label: Provide comprehensive development results including performance metrics (RMSE, MAE, R²), validation testing, and comparison to operational success criteria defined in Stage 1.
                type: textarea
    - policyEntityId: 202b7552-9f08-4d04-a1ef-b942ab659154
      name: Model Validation
      approvals:
        - policyEntityId: a18add31-0554-4d5f-90b5-3cafaae426be
          name: Model Validation Approval
          approvers:
            - editable: false
              name: modeling-review
              showByDefault: true
            - editable: false
              name: modeling-practitioners
              showByDefault: true
          evidence:
            id: Local.validation-signoff
            name: Model Validation Signoff
            description: Validation review checklist
            definition:
                - policyEntityId: 6c12791a-13b9-4063-a591-ad9ff6240a11
                  artifactType: input
                  details:
                    label: Have you reviewed the model validation reports and methodology?
                    options:
                        - label: "Yes"
                          value: "Yes"
                        - label: "No"
                          value: "No"
                    type: radio
                - policyEntityId: 5b06aa8b-cd06-4b82-a6ba-def092a7a409
                  artifactType: input
                  details:
                    label: Have you verified the regression performance metrics (RMSE, R²) meet thresholds?
                    options:
                        - label: "Yes"
                          value: "Yes"
                        - label: "No"
                          value: "No"
                    type: radio
                - policyEntityId: 0185ae81-b12a-493c-8ef1-54f2029394a0
                  artifactType: input
                  details:
                    label: Have you confirmed model interpretability meets operational requirements?
                    options:
                        - label: "Yes"
                          value: "Yes"
                        - label: "No"
                          value: "No"
                    type: radio
                - policyEntityId: b4be3b84-a646-4d66-9fa6-40117d7487b6
                  artifactType: input
                  details:
                    label: Do you certify this model meets O&G industry standards for operational deployment?
                    options:
                        - label: "Yes"
                          value: "Yes"
                        - label: "No"
                          value: "No"
                    type: radio
      evidenceSet:
        - id: Local.methodology-validation
          name: Methodology Validation
          description: Validate predictive model methodology and approach
          definition:
            - policyEntityId: 31d9245d-7d07-44d2-a97f-ed6085666a54
              artifactType: input
              aliasForClassification: methodology-validation
              details:
                label: Which predictive modeling methodology and framework is the model based on?
                type: textarea
            - policyEntityId: af4ffaed-2357-4e0e-9f3e-7fb57787139a
              artifactType: input
              aliasForClassification: methodology-fit
              details:
                label: Is the methodology fit for purpose and are all algorithmic choices properly justified for the O&G operational context?
                options:
                    - "Yes"
                    - "No"
                type: radio
            - policyEntityId: 93c60853-125f-4182-adb2-ec737ddc4c20
              artifactType: input
              aliasForClassification: data-quality-validation
              details:
                label: Are the input sensor data and operational parameters complete, accurate, relevant, and consistent with operational requirements?
                options:
                    - "Yes"
                    - "No"
                type: radio
            - policyEntityId: 51ed31c9-a56f-42bf-91c9-ee25b5ea4060
              artifactType: input
              aliasForClassification: interpretability-analysis
              details:
                label: Has the model owner performed interpretability and explainability analysis to ensure predictions can be understood by operations teams?
                options:
                    - "Yes"
                    - "No"
                type: radio
        - id: Local.model-quality-metrics
          name: Model Quality and Performance Assessment
          description: Assess model quality and performance metrics
          definition:
            - policyEntityId: f5130265-8e60-4f42-9001-64f9ffca587d
              artifactType: metadata
              details:
                metrics:
                    - aliases:
                        - RMSE
                        - root_mean_squared_error
                        - rmse_score
                      label: Root Mean Squared Error (RMSE)
                      name: rmse
                      threshold:
                        operator: <=
                        value: 0.15
                    - aliases:
                        - r2
                        - r_squared
                        - coefficient_of_determination
                      label: R-Squared (R²)
                      name: r2_score
                      threshold:
                        operator: '>='
                        value: 0.85
                type: modelmetric
            - policyEntityId: 33a01b3a-0c43-4dd8-81a3-4ade7a6fb472
              artifactType: policyScriptedCheck
              details:
                command: python /mnt/code/src/data-quality-check.py
                environmentId: 690e1a9c8a0ee66d0ee2369f
                hardwareTierId: small-k8s
                label: Data Quality and Drift Evaluation
                name: Data Quality and Drift Evaluation
                outputTypes:
                    - txt
                    - json
                parameters: []
                volumeSizeGiB: 10
            - policyEntityId: e19f83f4-1a50-4336-99e5-0aa69634b336
              artifactType: metadata
              details:
                label: Upload comprehensive model validation report
                type: file
        - id: Local.operational-readiness
          name: Operational Readiness Assessment
          description: Operational readiness and deployment assessment
          definition:
            - policyEntityId: 316d630f-4f72-4f70-ad54-f22650459f87
              artifactType: input
              aliasForClassification: operational-readiness
              details:
                label: Document operational readiness including integration with existing systems, monitoring procedures, alert thresholds, and incident response plans.
                type: textarea
    - policyEntityId: 055455a9-e18f-4cee-9f19-c43b5063b5bb
      name: Deployment Authorization and Monitoring
      approvals:
        - policyEntityId: b90c8040-32e4-483b-beb4-c1c69cc0bdfc
          name: Deployment Authorization
          approvers:
            - editable: false
              name: modeling-leadership
              showByDefault: true
            - editable: false
              name: modeling-review
              showByDefault: true
          evidence:
            id: Local.deployment-authorization-signoff
            name: Deployment Authorization Signoff
            description: Review and authorize deployment with monitoring
            definition:
                - policyEntityId: 1745ff12-6b25-4d97-a324-f842844b79d5
                  artifactType: input
                  details:
                    label: Have you reviewed and approved the deployment strategy and monitoring framework?
                    options:
                        - "Yes"
                        - "No"
                    type: radio
                - policyEntityId: 02692a39-c7cc-43f4-9e50-9193c4fdffad
                  artifactType: input
                  details:
                    label: Do you authorize deployment of this predictive model with required monitoring and governance controls?
                    options:
                        - "Yes"
                        - "No"
                    type: radio
      evidenceSet:
        - id: Local.deployment-strategy
          name: Deployment Strategy
          description: Define deployment strategy with monitoring
          definition:
            - policyEntityId: ed2ba2b4-5a58-4b5b-9d18-ce74a61c4e29
              artifactType: input
              aliasForClassification: deployment-strategy
              details:
                label: Outline deployment strategy including infrastructure requirements, continuous monitoring plans, performance tracking, and integration with operational systems (SCADA, DCS, etc.).
                type: textarea
        - id: Local.scalability-resilience
          name: Scalability and Resilience Plan
          description: Document system scalability and operational resilience
          definition:
            - policyEntityId: 5f285e0c-b8a3-463e-95d0-9d4d10d9eee0
              artifactType: input
              aliasForClassification: scalability-resilience
              details:
                label: Describe system scalability plans, operational resilience measures, and performance maintenance under varying operational conditions and sensor data volumes.
                type: textarea
        - id: Local.security-compliance
          name: Security and Compliance Measures
          description: Outline security and compliance measures
          definition:
            - policyEntityId: ce9b3982-2824-47e1-8661-d81fed2aa5e1
              artifactType: input
              aliasForClassification: security-compliance
              details:
                label: Detail security measures, data protection protocols, compliance with O&G cybersecurity requirements, and audit trail mechanisms.
                type: textarea
        - id: Local.continuous-monitoring
          name: Continuous Monitoring Framework
          description: Establish continuous monitoring and governance framework
          definition:
            - policyEntityId: 0feb23fe-1da6-4b60-a6f0-d55c9277a49a
              artifactType: input
              aliasForClassification: continuous-monitoring
              details:
                label: Define continuous monitoring framework including performance tracking, data drift detection, model degradation alerts, and regular review procedures.
                type: textarea
```
