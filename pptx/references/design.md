# Presentation Design Rules

Use these when building decks from scratch. If editing a branded template, follow the template — don't impose this system.

## Layout system (16:9)

- Slide: **10" × 5.625"**
- Safe margin: **≥ 0.5"** from every edge
- Gap between cards/blocks: **0.3–0.5"**
- Align columns to a consistent grid (e.g. left column x=0.5 w=4.3, right x=5.2 w=4.3)

## Every slide needs a visual anchor

Text-only title+bullets is the default bad AI slide. Prefer:

| Pattern | When |
|---------|------|
| Big number + label | KPIs, outcomes |
| Two-column (text + chart/image) | Explanations with evidence |
| 2×2 or 3-card row | Features, pillars, themes |
| Icon row (icon in circle + title + one line) | Process steps, benefits |
| Quote / callout band | Customer voice, thesis |
| Comparison columns | Before/after, us vs them |
| Timeline | Roadmap, history |

Vary the pattern across the deck. Never repeat the same layout 6 times.

## Typography

| Role | Size | Weight |
|------|------|--------|
| Slide title | 28–40pt | Bold |
| Section label | 12–14pt | Bold, uppercase, muted, letter-spaced |
| Body | 14–18pt | Regular |
| Big stat | 40–64pt | Bold |
| Caption / source | 10–12pt | Regular, muted |

- Left-align body and lists. Center only titles on title slides.
- One header font + one body font. Arial/Calibri/Inter-style is fine; pair serif headers only if intentional.
- High contrast: light text on dark or dark on light — never gray-on-gray.

## Color

Pick a palette of 4–6 colors and stick to it:

```
bg, surface/card, text, muted, accent, semantic (good/warn/bad)
```

Examples:

```javascript
// Dark executive
{ bg:"0B1220", card:"151E32", text:"F8FAFC", muted:"94A3B8", accent:"38BDF8", good:"34D399" }

// Clean light
{ bg:"F8FAFC", card:"FFFFFF", text:"0F172A", muted:"64748B", accent:"2563EB", good:"059669" }

// Bold startup
{ bg:"18181B", card:"27272A", text:"FAFAFA", muted:"A1A1AA", accent:"A78BFA", good:"4ADE80" }
```

Never default every deck to generic corporate blue. Match the topic.

## Spacing & density

- Prefer fewer words. One idea per slide.
- Titles ≤ 6 words when possible.
- Bullets ≤ 5 per slide, ≤ 12 words each.
- If content overflows, split the slide — don't shrink below readable sizes.

## Avoid (AI-slop tells)

- Accent underline bars under every title
- Decorative lines that don't align to a grid
- Clip art / random stock energy without purpose
- Low-contrast icons on busy backgrounds
- Walls of paragraph text
- "Agenda" slides with 12 items
- Footer collision with content
- Inconsistent card radii/shadows across slides

## Title slide formula

1. Strong title (large)
2. One-line subtitle or date/context (muted)
3. Optional thin accent or logo
4. Lots of negative space — don't fill it

## Closing slide

Clear next step or contact — not a dump of appendix links. Appendix slides go after if needed.
