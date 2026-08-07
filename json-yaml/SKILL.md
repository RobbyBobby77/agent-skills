---
name: json-yaml
description: >
  Create, validate, transform, and debug JSON, JSONC, YAML, TOML, and JSON
  Schema. Use for config files, OpenAPI fragments, CI configs, deep merges,
  schema validation, and converting between JSON/YAML/TOML. Do not use for
  general application business logic.
---

# JSON / YAML / TOML

## Workflow

1. Inspect the file format, schema, consumer, and repository formatting conventions.
2. Preserve comments, anchors, key order, and quoting when they are meaningful; PyYAML is not a round-trip editor.
3. Make the smallest structural change and avoid reformatting unrelated content.
4. Parse the result and validate it against the applicable schema or consuming tool.
5. Show semantic differences for risky configuration changes, not only textual diffs.

Use `ruamel.yaml` or a syntax-aware editor when YAML comments and presentation must survive.

## Parse & dump

```python
import json, yaml  # pip install pyyaml
from pathlib import Path

data = json.loads(Path("cfg.json").read_text())
Path("out.json").write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")

data = yaml.safe_load(Path("cfg.yaml").read_text())  # ALWAYS safe_load
Path("out.yaml").write_text(yaml.safe_dump(data, sort_keys=False, allow_unicode=True))
```

```bash
# jq
jq '.services.api.image' config.json
jq -r '.items[].id' data.json

# yq (mikefarah)
yq '.spec.replicas' deploy.yaml
yq -o=json '.' file.yaml > file.json
```

---

## YAML footguns

1. **`safe_load` only** — `load()` can execute code
2. **Unquoted `NO`, `on`, `off`** become booleans in YAML 1.1 — quote country codes / strings: `"NO"`
3. **Tabs illegal** for indentation — spaces only
4. **Indentation is structure** — validate with a parser after edits
5. **Anchors/aliases** (`&foo`, `*foo`) — powerful, easy to overuse
6. **Multiline**: `|` keeps newlines; `>` folds

```yaml
note: |
  line1
  line2
country: "NO"
enabled: true
```

---

## JSON rules

- No trailing commas (unless JSONC/JSON5 intentionally)
- No comments in strict JSON
- Numbers: no leading zeros; careful with big ints (JS precision)
- Prefer UTF-8; escape as needed

### JSONC (comments) → JSON

Strip comments carefully or use a JSONC-aware tool before strict parsers.

---

## JSON Schema (draft 2020-12 sketch)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://example.com/order.schema.json",
  "type": "object",
  "required": ["id", "items"],
  "additionalProperties": false,
  "properties": {
    "id": { "type": "string", "minLength": 1 },
    "items": {
      "type": "array",
      "minItems": 1,
      "items": {
        "type": "object",
        "required": ["sku", "qty"],
        "properties": {
          "sku": { "type": "string" },
          "qty": { "type": "integer", "minimum": 1 }
        },
        "additionalProperties": false
      }
    }
  }
}
```

```python
# pip install jsonschema
from jsonschema import validate
validate(instance=data, schema=schema)
```

---

## Deep merge (config layers)

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

Document whether arrays replace or concat (usually **replace**).

---

## TOML

```toml
[server]
port = 8080
host = "0.0.0.0"

[db]
url = "postgres://localhost/app"
```

```python
import tomllib  # py3.11+
tomllib.loads(Path("pyproject.toml").read_text())
```

Good for human-edited app config; YAML still dominates K8s/CI.

---

## Convert

```bash
yq -o=json '.' in.yaml > out.json
yq -P '.' in.json > out.yaml   # yaml pretty
python -c "import json,yaml,sys; yaml.safe_dump(json.load(sys.stdin), sys.stdout, sort_keys=False)"
```

---

## QA

- Round-trip parse after every edit
- `jq empty file.json` / `yaml.safe_load` for syntax
- Schema-validate when a schema exists
- Don't commit secrets — use env substitution patterns

## Pitfalls

- YAML norway problem (`NO` → false)
- Duplicate keys (last wins; some parsers error)
- Accidental type changes after round-tripping quoted scalars
- Giant single-line minified JSON — pretty-print for review then minify for prod if needed
- Mixing tabs/spaces in YAML
