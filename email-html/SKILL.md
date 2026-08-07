---
name: email-html
description: >
  Create and edit HTML emails: transactional, product, newsletter, and plain-text
  multipart alternatives. Use when the user wants email templates, .eml samples,
  MJML, responsive email HTML, or deliverability-conscious markup. Do not use for
  general web app UI (use normal frontend skills).
---

# HTML Email

Email clients are broken browsers (Outlook especially). Design for **constraint**, not chrome-dev-tools fidelity.

## Workflow

1. Identify message type, audience, sender identity, template variables, and target email clients.
2. Preserve an existing template's token syntax and delivery-platform requirements.
3. Build semantic content, responsive HTML, and an equivalent plain-text part.
4. Escape untrusted variable content and allow only expected URL schemes in links.
5. Compile/lint, inspect mobile and dark-mode renders, and report clients not actually tested.

## Stack choices

| Approach | When |
|----------|------|
| **Hand-rolled tables + inline CSS** | Max control, no build step |
| **MJML** | Preferred for new templates — compiles to solid HTML |
| **react-email / maizzle** | Product codebase already in JS |

```bash
npm install -g mjml
mjml input.mjml -o output.html
```

---

## Non-negotiables

1. **Table-based layout** for structure (or MJML that emits tables)
2. **Inline CSS** on elements — many clients strip `<style>`
3. **Width ~600px** content column (fluid wrapper OK)
4. **System fonts** first: `-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif`
5. **Always ship a plain-text part** for multipart
6. **Absolute image URLs** (or CID for embedded) — relative paths break
7. **Alt text** on every image
8. **No JavaScript**. Limited CSS: flex/grid unreliable; avoid external stylesheets
9. **Test dark mode** — avoid pure white/black only; use transparent PNGs carefully
10. **One clear CTA** — button as padded `<a>` (VML fallback for Outlook if critical)
11. **Accessible structure** — meaningful reading order, descriptive links, sufficient contrast, and `role="presentation"` on layout tables

---

## MJML skeleton

```mjml
<mjml>
  <mj-head>
    <mj-attributes>
      <mj-all font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif" />
      <mj-text font-size="16px" line-height="1.5" color="#1f2937" />
      <mj-button background-color="#2563eb" color="#ffffff" border-radius="6px" />
    </mj-attributes>
    <mj-preview>Your order shipped — tracking inside</mj-preview>
  </mj-head>
  <mj-body background-color="#f3f4f6">
    <mj-section background-color="#ffffff" padding="24px">
      <mj-column>
        <mj-image src="https://example.com/logo.png" alt="Acme" width="120px" align="left" />
        <mj-text font-size="22px" font-weight="700" padding-top="16px">Your order is on the way</mj-text>
        <mj-text>Hi {{first_name}}, package {{order_id}} shipped via {{carrier}}.</mj-text>
        <mj-button href="{{tracking_url}}">Track package</mj-button>
        <mj-text font-size="13px" color="#6b7280">If the button fails, copy: {{tracking_url}}</mj-text>
      </mj-column>
    </mj-section>
    <mj-section padding="16px">
      <mj-column>
        <mj-text font-size="12px" color="#9ca3af" align="center">
          Acme Inc · <a href="{{unsubscribe_url}}">Unsubscribe</a>
        </mj-text>
      </mj-column>
    </mj-section>
  </mj-body>
</mjml>
```

---

## Hand-rolled button (bulletproof-ish)

```html
<table role="presentation" cellspacing="0" cellpadding="0" border="0">
  <tr>
    <td bgcolor="#2563eb" style="border-radius:6px;">
      <a href="https://example.com"
         style="display:inline-block;padding:12px 24px;font-family:Arial,sans-serif;font-size:16px;color:#ffffff;text-decoration:none;border-radius:6px;">
        Confirm email
      </a>
    </td>
  </tr>
</table>
```

---

## Plain text alternative

```text
Subject: Your order is on the way

Hi Ada,

Package ORD-123 shipped via UPS.

Track: https://example.com/t/ORD-123

— Acme
Unsubscribe: https://example.com/unsub
```

Match the HTML content; don't leave "please view HTML" as the only body.

---

## Deliverability & content

- Subject ≤ ~60 chars; preview text earns the open
- Avoid spammy ALL CAPS, fake Re:/Fwd:, too many `!!!`
- Balance image-to-text; pure-image emails get filtered
- Include sender identity, address, and unsubscribe controls when applicable; confirm the governing legal requirements
- Never claim legal compliance from markup review alone
- Personalization tokens must have **fallback** defaults

---

## QA

1. Render HTML in browser + dark mode toggle
2. Check on mobile width (320–400px)
3. Validate links and UTM params
4. Send test to Gmail, Outlook.com, Apple Mail if possible
5. Tools: Litmus, Email on Acid, or free Mailtrap previews

## Pitfalls

- Outlook + padding on `<div>` / `<p>` — pad `<td>` instead
- `background-image` flaky in Outlook — solid colors safer
- Gap under images: `style="display:block"` on `<img>`
- Auto-linking phones/emails inconsistently — fine, don't fight it
