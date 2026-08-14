# Email client constraints

## CSS you may rely on (inline)

Safe: `color`, `background-color`, `font-family`, `font-size`, `font-weight`,
`line-height`, `text-align`, `text-decoration`, `padding` on `<td>`,
`border`, `border-radius` (ignored in some Outlook), `width`/`max-width`,
`display:block` on images.

Do not rely on: flexbox, grid, `gap`, `position`, `float` (fragile),
`<style>` in Gmail (partial), external stylesheets, web fonts as the only face,
`background-image` in Outlook desktop.

## Outlook desktop (Word)

- Pad `<td>`, never `<div>` / `<p>`
- `background-image` fails often — solid `bgcolor` / `background-color`
- VML for a button only when Outlook desktop is a listed target (see skill body)
- Widths in attributes + styles (`width="600"` and `style="width:600px"`)
- `border-collapse:collapse` on layout tables; `role="presentation"`
- MSO conditionals: `<!--[if mso]>…<![endif]-->`

## Gmail

- Clips very large HTML. Keep templates lean
- Strips or rewrites some `<style>` blocks — inline the important rules
- Image blocking is default for many users — alt text is the message
- Auto-links phones and emails; do not fight it

## Apple Mail / iOS

- Dark mode is aggressive. Pure `#000` on `#fff` (and the reverse) will invert badly
- Transparent PNG logos on a white header become white-on-white
- Prefer off-white / off-black (`#111` / `#f4f4f4`) and `bgcolor` on the wrapper

```html
<meta name="color-scheme" content="light dark">
<meta name="supported-color-schemes" content="light dark">
```

Those metas help; they do not save a white-only logo.

## Dark mode

- Never ship a message whose only contrast is black/white
- Test the logo on a dark canvas
- Do not put critical text inside an image
- If you set a dark `<style>` override, also keep inline colors readable without it

## Pre-send

```text
[ ] Subject + preheader
[ ] Plain-text part matches HTML
[ ] One primary CTA; absolute HTTPS
[ ] Images: alt + absolute URL; logo not wider than the content column
[ ] Footer identity; unsubscribe + address if marketing
[ ] Tokens have fallbacks; no leftover placeholders
[ ] 320px: no horizontal scroll
[ ] Dark mode: text and logo still visible
[ ] No JS, no required webfont
[ ] Test send to at least one real inbox when available
```
