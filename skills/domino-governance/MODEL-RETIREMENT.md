# Model retirement

Model owner archives the bundle, detaches policies, writes a final audit entry, marks the registered model retired or archived.

HTTP: [SKILL.md Configuration](./SKILL.md#configuration) (proxy → in-run gateway + access-token → public URL + PAT on 404; use the base where `GET $BASE/policy-overviews` returns HTTP 200).

## Core calls

```python
PATCH /bundles/{bundle_id} {"state": "Archived"}
```

Registered model retirement is a model-registry call (e.g. `/api/registeredmodels/v1/{modelName}`), not governance.

## Gotchas

- Archiving a bundle blocks new evidence submissions (state guard).
- Detaching policies does not delete the policy.
- Registered model retirement is a model-registry call, not governance.
