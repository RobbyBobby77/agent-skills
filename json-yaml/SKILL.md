---
name: json-yaml
description: >
  Edit, validate, convert, and debug JSON, JSONC, YAML, TOML, and JSON Schema
  without destroying comments, key order, or types. Use for config, OpenAPI
  fragments, CI/Kubernetes manifests, deep merges, and schema checks. Prefer
  api when the file is an HTTP contract you are changing for compatibility;
  do not use for application business logic.
---

# JSON / YAML / TOML

Agents run PyYAML `dump` over a Helm values file and silently turn `NO` into
`false`, drop comments, and reorder keys. This skill exists to stop that.

## Related skills

| Need | Skill |
|------|-------|
| OpenAPI as an HTTP contract | `api` |
| Doc-site page frontmatter | `markdown` |
| Compose / container config | `docker` |

## Workflow

1. Inspect format, consumer, schema, and the repo's quoting/indent conventions.
2. Choose an editor that can keep what matters (comments, anchors, key order).
3. Change the smallest structure. Do not reformat the rest of the file.
4. Parse the result. Validate against the schema or the consuming tool.
5. For risky config, show a **semantic** diff, not only the textual one.

**Hard rules**
- YAML: `safe_load` only. `yaml.load` is a code-execution bug.
- YAML that must keep comments or styling: `ruamel.yaml` (or a syntax-aware edit). PyYAML is a data round-trip, not an editor.
- Quote YAML scalars that are country codes, `on`/`off`/`yes`/`no`/`null`, versions that look like numbers, and anything the consumer expects as a string.
- Do not sort keys unless the consumer requires it.
- Do not commit secrets. Prefer env-substitution patterns the repo already uses.

---

## Choose a parser

| File | Keep comments / order? | Tool |
|------|------------------------|------|
| Strict JSON | order yes, comments no | `json` stdlib, `jq` |
| JSONC / JSON5 | comments yes | JSONC-aware tool, then emit strict JSON if the consumer needs it |
| YAML config / k8s / CI | **yes** | `ruamel.yaml`, or edit text in place and `safe_load` to verify |
| YAML as data only | no | `yaml.safe_load` / `safe_dump(sort_keys=False)` |
| TOML | order mostly | `tomllib` to read (py3.11+); a TOML writer if you must emit |

```python
from pathlib import Path
import json

data = json.loads(Path("cfg.json").read_text())
Path("out.json").write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")
```

```python
from ruamel.yaml import YAML  # pip install ruamel.yaml
yaml = YAML()
yaml.preserve_quotes = True
path = Path("values.yaml")
data = yaml.load(path.read_text())
data["replicaCount"] = 3
with path.open("w") as f:
    yaml.dump(data, f)
```

```bash
jq empty config.json
yq '.spec.replicas' deploy.yaml          # mikefarah yq
yq -o=json '.' file.yaml > file.json
```

Footguns (Norway, duplicate keys, k8s, JSONC): [references/footguns.md](references/footguns.md).

---

## JSON

- No trailing commas, no comments, no `NaN`/`Infinity` in strict JSON
- Integers above `2^53-1` are not safe in JavaScript — keep them as strings if a JS consumer exists
- UTF-8. `ensure_ascii=False` unless the consumer requires escapes

JSONC → JSON: strip comments with a JSONC parser. Do not regex-strip `//` inside strings.

---

## Schema

Validate when a schema exists. Do not invent `additionalProperties: false` on a public API that already allows extras.

```python
from jsonschema import validate
validate(instance=data, schema=schema)
```

---

## Merge

```python
def deep_merge(base: dict, override: dict) -> dict:
    out = dict(base)
    for k, v in override.items():
        if k in out and isinstance(out[k], dict) and isinstance(v, dict):
            out[k] = deep_merge(out[k], v)
        else:
            out[k] = v
    return out
```

Arrays **replace** unless the repo already concatenates. Document which. Kubernetes strategic merge is not this function — do not fake it.

---

## TOML

```python
import tomllib
tomllib.loads(Path("pyproject.toml").read_text())
```

Good for human-edited app config. YAML still dominates k8s/CI. `tomllib` is read-only; do not dump TOML via a YAML serializer.

---

## Verify

```text
[ ] Parses with the same class of parser the consumer uses
[ ] Comments / key order / quoting preserved when they were meaningful
[ ] Types unchanged (string "NO" is still a string)
[ ] Schema or consuming tool accepts the file
[ ] Semantic diff reviewed for anything that changes runtime behavior
[ ] No secrets introduced
```
