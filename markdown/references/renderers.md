# Renderer differences

Use this when the target is a specific host or doc site. Do not mix these syntaxes on one page.

## Heading slugs

Same heading, three different fragment IDs:

| Heading | GitHub | GitLab | Docusaurus |
|---------|--------|--------|------------|
| `Foo & Bar` | `foo--bar` | `foo-bar` | `foo--bar` |
| `C++ API` | `c-api` | `c-api` | `c-api` |
| `What's next?` | `whats-next` | `what-s-next` | `whats-next` |
| `1. Install` | `1-install` | `1-install` | `1-install` |

GitHub: lowercase; strip punctuation except spaces/`-`; `&` becomes `-`; collapse spaces to `-`.

GitLab: lowercase; punctuation often becomes `-`; apostrophes are kept as `-` (`what-s-next`).

Docusaurus: similar to GitHub; custom IDs win: `## Install {#install}`.

If a URL is already published, keep the heading text or add an explicit `{#old-id}` / HTML `<a name>` rather than breaking the slug.

## Callouts / admonitions

```markdown
<!-- GitHub (and many GFM previews) -->
> [!NOTE]
> Context.
> [!WARNING]
> Footgun.
> [!IMPORTANT]
> Must read.

<!-- MkDocs Material -->
!!! note
    Context.

<!-- Docusaurus MDX -->
:::note
Context.
:::

<!-- VitePress -->
::: warning
Footgun.
:::
```

Never emit `[!NOTE]` inside an MkDocs or Docusaurus tree. Never emit `!!! note` in a GitHub README.

## MDX / JSX traps

In Docusaurus and other MDX pipelines:

- `{` `}` in prose start expressions — wrap or escape: `` {`{id}`} `` or use `{'{'}`
- `<foo>` looks like JSX — use backticks for placeholders: `` `<cluster-id>` ``
- Raw HTML comments are not always safe; prefer `{/* comment */}` only in MDX files
- Import diagrams as components or fenced Mermaid only if that site's plugin is already enabled

## Frontmatter

```yaml
---
title: Install
description: Install the CLI
# sidebar_position / nav_order / slug — only keys the site already uses
---
```

Do not invent a frontmatter schema. Copy keys from a sibling page. Validate YAML with the `json-yaml` skill if comments or anchors must survive.

## What each host will not do

- GitHub README: no guaranteed sidebar, no MDX, mermaid yes (limited), `[!NOTE]` yes
- GitHub wiki: different relative-link root than the repo
- GitLab: mermaid yes; wiki links are not repo paths
- MkDocs: nav in `mkdocs.yml` is source of truth — a new page that is not listed is invisible
- Docusaurus: sidebar config or `_category_.json` must mention new docs
- Slack/email: treat as one-shot GFM; inline the command, do not link `docs/foo.md`
