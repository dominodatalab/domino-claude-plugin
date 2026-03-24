# Example Domino Governance Policy: EU AI Act Compliance

This is a real-world production policy for EU AI Act compliance. Use it as a structural
reference when generating policy YAML. It demonstrates patterns beyond the basic schema
documentation, including advanced features you should replicate.

## Key Patterns to Follow

### 1. policyEntityId on Everything
Every stage, evidence set item, approval, and individual artifact gets a unique UUID via
`policyEntityId`. Generate fresh UUIDs (v4 format) for every element. Place `policyEntityId`
as the FIRST key in each object.

### 2. aliasForClassification is Used Broadly
In this policy, nearly every input artifact has an `aliasForClassification` field, not just
the ones directly used in classification rules. The alias is typically a kebab-case slug of
the label text. This enables the classification engine to reference any input if needed.

Pattern: `aliasForClassification: kebab-case-version-of-the-label`

### 3. conditionalDisplay for Dynamic Forms
Instead of top-level `visibility` rules on evidence sets, individual artifacts can use
`conditionalDisplay` to show/hide based on another input's value:

```yaml
details:
  conditionalDisplay:
    dependsOn: Local.<evidence-set-id>
    showIfValue: "Some Option"     # single value
    # OR
    showIfValues:                   # multiple values
      - "Option A"
      - "Option B"
```

### 4. Evidence Set Structure Within Stages
Each stage contains an `evidenceSet` array (not just `evidence`). Each evidence set item has:
- `id`: Local.<kebab-case-id>
- `name`: Display name
- `description`: What this evidence section covers
- `definition`: Array of artifacts

### 5. Approval Structure
Approvals are nested within each stage with their own evidence:

```yaml
approvals:
  - policyEntityId: <uuid>
    name: "Stage Name Sign Off"
    approvers:
      - name: model-gov-org     # or your-org-name as placeholder
        showByDefault: true
        editable: false
    evidence:
      id: Local.<signoff-id>
      name: "<Stage> Approval"
      description: "Review and approve..."
      definition:
        - artifactType: input
          details:
            label: "Do you approve?"
            options:
              - Approved
              - Approved with Conditions
              - Not Approved
            type: radio
```

### 6. Classification Rule Reference
The classification block at top level can reference a named rule:

```yaml
classification:
  rule: EU-AI-ACT
```

Or use an inline Go-like expression as shown in the schema reference.

### 7. Scripted Checks
Real scripted checks include `command`, `environmentId`, `hardwareTierId`, output types,
and `volumeSizeGiB`:

```yaml
- artifactType: policyScriptedCheck
  details:
    command: path/to/script.py
    name: Check Name
    label: Check Display Label
    environmentId: <env-id>
    hardwareTierId: small-k8s
    outputTypes:
      - json
      - png
      - html
    volumeSizeGiB: 4
```

### 8. Metrics Checks
Model quality metrics with aliases and thresholds:

```yaml
- artifactType: metadata
  details:
    type: modelmetric
    metrics:
      - name: Accuracy
        label: Model Accuracy
        aliases:
          - acc
          - accuracy_score
        threshold:
          operator: '>='
          value: 0.85
```

### 9. Stage Naming Convention
Stages use descriptive names without numbering prefixes:
- "AI System Classification and Risk Assessment"
- "Legal Basis and Compliance Requirements"
- "AI System Development and Documentation"
- "Risk Management and Safety Measures"
- "Independent Conformity Assessment"
- "Transparency and User Information"
- "Deployment and Post-Market Monitoring"
- "Executive Approval and EU AI Act Compliance"

### 10. Final Executive Stage Pattern
The last stage typically consolidates all prior approvals with a summary review:
- Re-collects status of each prior stage (Approved/Approved with Conditions/Not Approved/Pending)
- Includes an executive summary textarea
- Has both executive management AND board-level sign-offs
- Board sign-off is conditionally displayed for high-risk systems only

---

## Full Example YAML

```yaml
classification:
  rule: EU-AI-ACT
stages:
  - policyEntityId: 417a056f-fea3-4300-840a-e2c074d68633
    name: AI System Classification and Risk Assessment
    evidenceSet:
      - description: Define the AI system according to EU AI Act requirements
        definition:
          - policyEntityId: 45f316e1-0a24-4393-9826-1d10aee1455c
            artifactType: input
            aliasForClassification: >-
              provide-a-detailed-description-of-the-ai-system-and-its-intended-purpose
            details:
              label: >-
                Provide a detailed description of the AI system and its intended
                purpose
              placeholder: >-
                Describe the AI system's functionality, intended use, users, and
                how it operates to achieve its objectives...
              type: textarea
        id: Local.ai-system-definition
        name: AI System Definition
      - description: Classify the AI system according to EU AI Act categories
        definition:
          - policyEntityId: 81195069-4620-4d60-815a-f309cb45c59e
            artifactType: input
            aliasForClassification: select-the-primary-ai-system-category
            details:
              label: Select the primary AI system category
              options:
                - Prohibited AI System
                - High-Risk AI System
                - General Purpose AI (GPAI) Model
                - Limited Risk AI System
                - Minimal Risk AI System
                - AI System for General Purpose
              type: select
        id: Local.ai-system-category
        name: AI System Category
      - description: >-
          Determine if the AI system falls under high-risk categories per Annex
          III
        definition:
          - policyEntityId: a5ffd8a9-4f0d-4694-b837-ab9d96f823ea
            artifactType: input
            aliasForClassification: select-all-applicable-high-risk-ai-system-categories-(annex-iii)
            details:
              label: Select all applicable high-risk AI system categories (Annex III)
              options:
                - Biometric identification and categorisation of natural persons
                - Management and operation of critical infrastructure
                - Education and vocational training
                - Employment, workers management and access to self-employment
                - >-
                  Access to and enjoyment of essential private services and
                  public services and benefits
                - Law enforcement
                - Migration, asylum and border control management
                - Administration of justice and democratic processes
                - Credit scoring and creditworthiness evaluation
                - Risk assessment and pricing for insurance
                - None of the above apply
              type: checkbox
        id: Local.high-risk-classification
        name: High-Risk AI System Classification
      - description: Verify the AI system does not engage in prohibited practices
        definition:
          - policyEntityId: 6b24283a-c11d-4cf9-b95e-e1fe719f37b7
            artifactType: input
            aliasForClassification: confirm-the-ai-system-does-not-engage-in-any-prohibited-practices
            details:
              label: >-
                Confirm the AI system does NOT engage in any prohibited
                practices
              options:
                - >-
                  Does not use subliminal techniques or manipulative/deceptive
                  techniques
                - Does not exploit vulnerabilities of specific groups
                - Does not perform social scoring by public authorities
                - >-
                  Does not use real-time biometric identification in public
                  spaces (except permitted law enforcement)
                - >-
                  Does not perform biometric categorisation based on sensitive
                  characteristics
                - >-
                  Does not perform emotion recognition in workplace/education
                  (except safety/medical)
                - Confirmed - System does not engage in prohibited practices
              type: checkbox
        id: Local.prohibited-check
        name: Prohibited AI Practices Check
      - description: Determine if this is a GPAI model requiring specific obligations
        definition:
          - policyEntityId: 053bbf93-3676-4e8b-98b7-26c27e2afdcd
            artifactType: input
            aliasForClassification: is-this-a-general-purpose-ai-(gpai)-model
            details:
              label: Is this a General Purpose AI (GPAI) model?
              options:
                - Yes - Foundation model with general capabilities
                - Yes - Systemic risk model (>10^25 FLOPs)
                - No - Specific purpose AI system
              type: radio
          - policyEntityId: fce8b040-041c-4423-a557-99b7a1f70be0
            artifactType: input
            aliasForClassification: if-gpai-estimate-compute-used-for-training-(flops)
            details:
              conditionalDisplay:
                dependsOn: Local.gpai-model-check
                showIfValue: Yes - Foundation model with general capabilities
              label: If GPAI, estimate compute used for training (FLOPs)
              options:
                - Less than 10^25 FLOPs
                - Greater than 10^25 FLOPs (Systemic Risk)
                - Unknown/Not Applicable
              type: select
        id: Local.gpai-model-check
        name: General Purpose AI Model Assessment
      - description: Assess the overall risk level of the AI system
        definition:
          - policyEntityId: a6c254a4-af7a-4bf2-aa57-d8e477262123
            artifactType: input
            aliasForClassification: based-on-eu-ai-act-criteria-what-is-the-risk-level
            details:
              label: Based on EU AI Act criteria, what is the risk level?
              options:
                - Unacceptable Risk (Prohibited)
                - High Risk (Annex III or CE marked)
                - Limited Risk (Transparency obligations)
                - Minimal Risk (No specific obligations)
              type: radio
        id: Local.risk-level-assessment
        name: Risk Level Assessment
      - description: Identify intended users and use cases
        definition:
          - policyEntityId: 42d8d9c3-ae4b-4ba2-b178-56e21af66c8b
            artifactType: input
            aliasForClassification: select-all-intended-user-categories
            details:
              label: Select all intended user categories
              options:
                - General Public/Consumers
                - Professional Users
                - Public Authorities
                - Law Enforcement
                - Healthcare Professionals
                - Educational Institutions
                - Financial Services
                - Employers/HR Departments
                - Other Businesses
                - Internal Use Only
              type: checkbox
        id: Local.intended-users
        name: Intended Users and Use Cases
      - description: Define the geographic scope of deployment
        definition:
          - policyEntityId: 2a3d31b8-d41e-402a-a8ad-4034335de149
            artifactType: input
            aliasForClassification: select-all-applicable-geographic-regions
            details:
              label: Select all applicable geographic regions
              options:
                - European Union
                - European Economic Area
                - United Kingdom
                - United States
                - Canada
                - Other International Markets
                - Global Deployment
              type: checkbox
        id: Local.geographic-scope
        name: Geographic Scope
      - description: Assess potential impact on fundamental rights
        definition:
          - policyEntityId: 904feaba-cdc6-4ba8-b3b2-2cb0833928fc
            artifactType: input
            aliasForClassification: rate-potential-impact-on-fundamental-rights
            details:
              label: Rate potential impact on fundamental rights
              options:
                - High Impact (significant effects on rights)
                - Medium Impact (moderate effects on rights)
                - Low Impact (minimal effects on rights)
                - No Impact (no effects on fundamental rights)
              type: radio
        id: Local.fundamental-rights-assessment
        name: Fundamental Rights Impact Assessment
    approvals:
      - policyEntityId: 68f354f0-05f9-4770-b2e9-7e32a2e87223
        name: AI System Classification Sign Off
        approvers:
          - name: model-gov-org
            showByDefault: true
            editable: false
        evidence:
          description: Review and approve the AI system classification
          definition:
            - policyEntityId: 7b850856-0556-4fbf-9e5b-b415deae5ded
              artifactType: input
              details:
                label: >-
                  Do you approve the AI system classification and risk
                  assessment?
                options:
                  - Approved as Classified
                  - Approved with Modified Classification
                  - Not Approved - Requires Reclassification
                type: radio
            - policyEntityId: 5d26b6a0-1064-42f0-b5b0-07addc1a79ce
              artifactType: input
              details:
                conditionalDisplay:
                  dependsOn: Local.classification-signoff
                  showIfValue: Approved with Modified Classification
                label: If classification modified, select new risk level
                options:
                  - Unacceptable Risk (Prohibited)
                  - High Risk
                  - Limited Risk
                  - Minimal Risk
                type: radio
          id: Local.classification-signoff
          name: Classification Approval
  - policyEntityId: 514606e9-b263-46af-85ba-0c36b2138451
    name: Legal Basis and Compliance Requirements
    evidenceSet:
      - description: >-
          Establish legal basis for AI system operation under GDPR and other
          laws
        definition:
          - policyEntityId: eebd7b3f-255e-4918-b56f-2451d0bac0c1
            artifactType: input
            aliasForClassification: select-primary-legal-basis-for-data-processing
            details:
              label: Select primary legal basis for data processing
              options:
                - Consent (GDPR Art. 6(1)(a))
                - Contract (GDPR Art. 6(1)(b))
                - Legal Obligation (GDPR Art. 6(1)(c))
                - Vital Interests (GDPR Art. 6(1)(d))
                - Public Task (GDPR Art. 6(1)(e))
                - Legitimate Interests (GDPR Art. 6(1)(f))
                - Not Applicable (no personal data)
              type: select
        id: Local.legal-basis
        name: Legal Basis for Processing
      - description: Identify all applicable regulatory requirements
        definition:
          - policyEntityId: 2397687b-d930-4735-92f6-9de5d09bcf68
            artifactType: input
            aliasForClassification: select-all-applicable-regulatory-frameworks
            details:
              label: Select all applicable regulatory frameworks
              options:
                - EU AI Act
                - GDPR (General Data Protection Regulation)
                - Digital Services Act (DSA)
                - Digital Markets Act (DMA)
                - Digital Operational Resilience Act (DORA)
                - Medical Device Regulation (MDR)
                - Consumer Protection Directives
                - Financial Services Regulations
                - Employment Law
                - Non-Discrimination Law
                - Cybersecurity Act
                - Product Liability Directive
                - Other National Laws
              type: checkbox
        id: Local.applicable-regulations
        name: Applicable Regulations
      - description: Conduct DPIA if required for high-risk processing
        definition:
          - policyEntityId: ac7f2985-8563-4ca7-a303-dd701dc9035a
            artifactType: input
            aliasForClassification: is-a-data-protection-impact-assessment-(dpia)-required
            details:
              label: Is a Data Protection Impact Assessment (DPIA) required?
              options:
                - Yes - High risk to rights and freedoms
                - No - Not required
                - Uncertain - Legal review needed
              type: radio
          - policyEntityId: aa5057c4-e939-4387-9fa9-98287ab2784b
            artifactType: input
            aliasForClassification: path-to-completed-dpia-documentation-in-domino
            details:
              conditionalDisplay:
                dependsOn: Local.data-protection-impact
                showIfValue: Yes - High risk to rights and freedoms
              label: Path to completed DPIA documentation in Domino
              placeholder: Enter path to DPIA documentation if required...
              type: textarea
        id: Local.data-protection-impact
        name: Data Protection Impact Assessment
      - description: Assess processing of special categories of personal data
        definition:
          - policyEntityId: 5d1a8dc3-9136-4672-8750-c6a382a907a7
            artifactType: input
            aliasForClassification: does-the-ai-system-process-special-categories-of-personal-data
            details:
              label: Does the AI system process special categories of personal data?
              options:
                - Racial or ethnic origin data
                - Political opinions data
                - Religious or philosophical beliefs data
                - Trade union membership data
                - Genetic data
                - Biometric data for unique identification
                - Health data
                - Sex life or sexual orientation data
                - None of the above
              type: checkbox
        id: Local.special-category-data
        name: Special Category Data Processing
      - description: Assess processing of children's data
        definition:
          - policyEntityId: b0d17d04-e418-40fb-8bd2-ba22f9d7ec74
            artifactType: input
            aliasForClassification: does-the-ai-system-process-data-of-children-(under-18)
            details:
              label: Does the AI system process data of children (under 18)?
              options:
                - Yes - Specifically targets children
                - Yes - May incidentally process children's data
                - No - Does not process children's data
              type: radio
        id: Local.children-data
        name: Children's Data Processing
      - description: Document international data transfer arrangements
        definition:
          - policyEntityId: da35adeb-5c9f-4bda-8617-dd6e35a53cef
            artifactType: input
            aliasForClassification: select-all-applicable-transfer-mechanisms
            details:
              label: Select all applicable transfer mechanisms
              options:
                - Adequacy Decision
                - Standard Contractual Clauses (SCCs)
                - Binding Corporate Rules (BCRs)
                - Certification/Codes of Conduct
                - Derogations for specific situations
                - No international transfers
              type: checkbox
        id: Local.international-transfers
        name: International Data Transfers
      - description: Identify third-party data processors and AI providers
        definition:
          - policyEntityId: db9cd6c5-5eb3-4ca9-8684-911f5ba1582c
            artifactType: input
            aliasForClassification: document-third-party-processors-and-ai-service-providers
            details:
              label: Document third-party processors and AI service providers
              placeholder: >-
                List all third-party processors, their roles, and data
                processing agreements...
              type: textarea
        id: Local.third-party-processors
        name: Third-Party Data Processors
    approvals:
      - policyEntityId: b4e2b4de-9ff3-49c3-a51f-54e5e026e38c
        name: Legal and Compliance Foundation Sign Off
        approvers:
          - name: model-gov-org
            showByDefault: true
            editable: false
        evidence:
          description: Review and approve legal basis and compliance framework
          definition:
            - policyEntityId: 1bcb28fc-b7e8-4b0e-900f-ef505553f713
              artifactType: input
              details:
                label: Is the legal basis and compliance framework adequate?
                options:
                  - Approved - Comprehensive compliance framework
                  - Approved with conditions
                  - Not Approved - Insufficient legal basis
                type: radio
          id: Local.legal-foundation-signoff
          name: Legal Foundation Approval
  # ... (remaining stages follow the same patterns)
  # See the full YAML below for all 8 stages
```

## Structural Summary

The full policy contains **8 stages** in sequence:

1. **AI System Classification and Risk Assessment** — 9 evidence sets covering system
   definition, category classification, high-risk checks, prohibited practices, GPAI assessment,
   risk level, intended users, geographic scope, and fundamental rights impact.

2. **Legal Basis and Compliance Requirements** — 7 evidence sets covering GDPR legal basis,
   applicable regulations, DPIA, special category data, children's data, international transfers,
   and third-party processors.

3. **AI System Development and Documentation** — 11 evidence sets covering methodology,
   training data sources, data governance, bias mitigation, model architecture, performance
   metrics, limitations, project links, code repos, technical docs, and quality metrics (automated).

4. **Risk Management and Safety Measures** — 5 evidence sets covering risk management system,
   safety/security measures, human oversight, accuracy/robustness testing, and incident reporting.

5. **Independent Conformity Assessment** — 8 evidence sets covering scope, independence,
   technical doc review, bias/fairness assessment, automated bias check (scripted), performance
   assessment, transparency assessment, findings, and remediation plan.

6. **Transparency and User Information** — 5 evidence sets covering transparency obligations,
   user information, disclosure mechanisms, explainability measures, and AI-generated content
   labeling.

7. **Deployment and Post-Market Monitoring** — 7 evidence sets covering deployment plan,
   post-market monitoring, monitoring frequency, update procedures, serious incident reporting,
   market surveillance cooperation, and Domino monitoring dashboard link.

8. **Executive Approval and EU AI Act Compliance** — 16 evidence sets consolidating all prior
   stage statuses, compliance summary, CE marking, EU database registration, notified body
   assessment, fundamental rights impact, risk mitigation effectiveness, executive summary,
   market placement readiness, ongoing obligations, and executive/board presentations.
   Includes BOTH executive management AND board of directors sign-offs.

## Patterns for the Skill to Replicate

When generating new policies, follow these structural conventions from this example:

1. **Generate UUIDs** for every `policyEntityId` using Python's `uuid.uuid4()`
2. **Add `aliasForClassification`** to every input artifact, using a kebab-case slug of the label
3. **Use `evidenceSet` array** within stages (not flat `evidence`)
4. **Each evidence set** gets its own `id`, `name`, `description`, and `definition`
5. **Approval evidence** uses the pattern: radio with Approved/Approved with Conditions/Not Approved
6. **Use `conditionalDisplay`** for fields that depend on other answers
7. **Include a final executive stage** that consolidates all prior stage statuses
8. **Naming**: stages use descriptive names, evidence sets use `Local.<kebab-case>`, approvals end with "Sign Off"
9. **Approver block**: `name: model-gov-org, showByDefault: true, editable: false` (use placeholder org name)
10. **Textarea placeholders** provide concrete guidance on what to write
