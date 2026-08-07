# Mermaid Patterns

## Class diagram

```mermaid
classDiagram
  class User {
    +UUID id
    +String email
    +login()
  }
  class Order {
    +UUID id
    +Money total
  }
  User "1" --> "*" Order : places
```

## Gantt

```mermaid
gantt
  title Launch plan
  dateFormat YYYY-MM-DD
  section Build
  API     :a1, 2026-03-01, 14d
  Web     :a2, after a1, 10d
  section Ship
  Beta    :2026-03-25, 7d
```

## Git graph

```mermaid
gitGraph
  commit id: "init"
  branch feature
  checkout feature
  commit id: "wip"
  checkout main
  merge feature
```

## Mindmap

```mermaid
mindmap
  root((Product))
    Acquire
      Ads
      Viral
    Activate
      Onboarding
    Revenue
      Subs
```

## Pie

```mermaid
pie showData
  title Share
  "Pro" : 55
  "Basic" : 30
  "Free" : 15
```

## Styling tips

```mermaid
flowchart LR
  A[OK] --> B{Gate}
  B -->|yes| C[Go]
  B -->|no| D[Stop]
  style C fill:#86efac
  style D fill:#fca5a5
```

## Escaping

- Node text with parens/brackets: `A["process (main)"]`
- Edge labels with special chars: `A -->|"a → b"| B`
- Never use `end` as an id; use `endNode`
