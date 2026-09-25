# Onboard a model into governance

Model owner resolves the project and registered model, creates or reuses a policy, creates a bundle, attaches the ModelVersion, fills the first evidence slot, and submits.

HTTP: [SKILL.md Configuration](./SKILL.md#configuration) (proxy → in-run gateway + access-token → public URL + PAT on 404; use the base where `GET $BASE/policy-overviews` returns HTTP 200).

## Core calls

```python
bundle = POST /bundles {
    "name": bundle_name,
    "projectId": project_id,
    "policyId": policy_id,
    "attachments": [
        {"type": "ModelVersion", "identifier": {"name": registered_model_name, "version": model_version}}
    ],
}
# or create without attachments, then POST /bundles/{id}/attachments

POST /rpc/compute-policy {"bundleId": bundle_id, "policyId": policy_id}
# poll GET /results/latest?bundleID=bundle_id (SKILL.md "After compute-policy (polling)")

POST /rpc/submit-result-to-policy {"bundleId": bundle_id, "policyId": policy_id, **evidence}
```

## Gotchas

- Create Bundle is disabled until a policy is **Published**.
- Attachment `identifier.name` for `ModelVersion` is the MLflow registered model name, not a Domino UUID.
- Draft evidence is not submitted; text sections need an explicit `submit-result-to-policy` to become `isLatest=true`.
- One model can attach to multiple bundles (multi-policy: ML + Agentic + EU AI Act).
