# Policy lifecycle and rollout

Policy admin drafts a policy, creates a version, PUTs the definition (escaped YAML), publishes, bulk-attaches to in-scope bundles, triggers re-evidence, retires the old version.

HTTP: [SKILL.md Configuration](./SKILL.md#configuration) (proxy → in-run gateway + access-token → public URL + PAT on 404; use the base where `GET $BASE/policy-overviews` returns HTTP 200).

## Core calls

```python
POST /policies {"name": policy_name}

POST /policies/{policy_id}/versions
# 409 if a draft version already exists; treat as idempotent

PUT /policies/{policy_id}/definition {"definition": definition_yaml_string}

PUT /policies/{policy_id}/status {"status": "Published"}

POST /rpc/add-policies-to-bundle {"bundleId": bundle_id, "policyIds": [policy_id]}
```

## Gotchas

- PUT definition takes an escaped YAML string.
- Publishing a version does not auto-attach to existing bundles; bulk attach is a separate RPC (`add-policies-to-bundle`).
- Retiring a version does not detach from bundles already on it.
- Composition: lifecycle + regulation + cross-cutting policies all apply simultaneously on one bundle.
