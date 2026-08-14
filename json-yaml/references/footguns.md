# Config footguns

## YAML 1.1 implicit types (the Norway problem)

Unquoted, these become booleans or null in YAML 1.1 (PyYAML, many k8s paths):

`y`, `n`, `yes`, `no`, `true`, `false`, `on`, `off`, `null`, `~`,
`NO`, `On`, country `NO`, `off` as a feature flag string.

```yaml
country: "NO"
debug: "off"      # if the consumer wants the string
enabled: true     # real boolean, unquoted is fine
version: "1.10"   # unquoted 1.10 may become a float
```

Quote any scalar you are not certain is a real boolean, null, or number.

## Duplicate keys

Last key usually wins. Some parsers error. `ruamel` can warn. Never rely on duplicates as an overlay mechanism.

## Tabs and indentation

Tabs are illegal for YAML indentation. A single wrong indent re-nests a whole block. Always re-parse after a hand edit.

## Anchors

`&foo` / `*foo` are by-reference. Overlays that mutate an alias mutate every use. Prefer explicit copies in CI/k8s unless the file already uses anchors.

## Round-trip type drift

PyYAML `safe_dump` will:

- drop comments
- drop explicit quotes
- optionally sort keys (`sort_keys=False` is mandatory)
- rewrite multiline style
- turn a quoted `"NO"` into a boolean on the next `safe_load` if you dumped it unquoted

If comments or quoting matter, you never went through PyYAML as an editor.

## Kubernetes / Helm / CI

- Helm `values.yaml` is YAML 1.1. Country codes, `off`, `NO` must be quoted.
- `yes` as a replica count or feature name will become `true`.
- Do not run the generic `deep_merge` on k8s objects and expect strategic-merge-patch semantics (list merge keys, `$patch`, etc.).
- GitHub Actions: unquoted `on:` is the trigger map; a job named `on` is a footgun. `on` as a string value must be quoted.
- Huge single-line kube manifests: pretty-print for review, do not commit a reflow the user did not ask for.

## JSONC

`tsconfig.json`, VS Code settings, some OpenAPI preprocessors.

1. Parse with a JSONC-aware tool
2. Edit
3. Emit what the consumer accepts (JSONC if it is JSONC; strict JSON if tsc/CI will `JSON.parse`)

Never strip `//` with a regex. `"https://example.com"` will break.

## Big integers

JS `JSON.parse` silently loses integers past `Number.MAX_SAFE_INTEGER`. If a JS tool will read the file, keep large IDs as strings.

## Secrets

Scan dumps and diffs for tokens, private keys, connection strings. Replace with the repo's existing substitution (`${VAR}`, `env:`, SealedSecret, etc.). Do not invent a new secret scheme.
