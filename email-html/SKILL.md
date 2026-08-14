---
name: email-html
description: >
  Build and edit HTML email that survives Outlook, Gmail, and Apple Mail:
  transactional, product, newsletter, MJML, and a matching plain-text part.
  Use when the user wants an email template, .eml sample, or deliverability-
  conscious markup. Preserve the ESP's existing token syntax. Do not use for
  general web app UI.
---

# HTML Email

Chrome is not the client. Outlook (Word engine), Gmail (stripped CSS), and
dark mode will each break a "correct" page. This skill exists for those
constraints.

## Related skills

| Need | Skill |
|------|-------|
| Surrounding product docs | `markdown` |
| Calendar invite attachment | `ics` |
| Image assets / diagrams | `diagrams` |

## Workflow

1. Identify message type (transactional vs marketing), ESP, token syntax, and target clients.
2. **Preserve** the existing template's `{{handles}}` / `${vars}` / merge tags. Do not invent a new interpolator.
3. Build table layout + inline CSS + an equivalent plain-text part.
4. Escape untrusted variables. Allow only `https:` (and `mailto:`) in hrefs.
5. Compile if MJML, render at 320px and in dark mode, report clients you did not test.

**Hard rules**
- No JavaScript. No web fonts required for the core message.
- Layout is tables (or MJML that emits tables). Flex/grid are decoration at best.
- CSS that matters is inline. Many clients drop `<style>`.
- Images are absolute HTTPS (or CID). Every image has alt text.
- One primary CTA. Always a matching plain-text part.
- Do not claim CAN-SPAM / CASL / GDPR compliance from markup review.

Client CSS, Outlook VML, and dark mode: [references/clients.md](references/clients.md).

---

## Stack

| Approach | When |
|----------|------|
| **MJML** | New templates — preferred |
| **Hand-rolled tables + inline CSS** | No build step, or patching a given HTML file |
| **react-email / maizzle** | The product already uses it |

```bash
npm install -g mjml
mjml input.mjml -o output.html
```

---

## MJML

Keep the ESP tokens exactly as the existing template uses them. Give every token a fallback at send time.

```mjml
<mjml>
  <mj-head>
    <mj-preview>Your order shipped — tracking inside</mj-preview>
    <mj-attributes>
      <mj-all font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif" />
      <mj-text font-size="16px" line-height="1.5" color="#1f2937" />
      <mj-button background-color="#2563eb" color="#ffffff" border-radius="6px" />
    </mj-attributes>
  </mj-head>
  <mj-body background-color="#f3f4f6">
    <mj-section background-color="#ffffff" padding="24px">
      <mj-column>
        <mj-image src="https://example.com/logo.png" alt="Acme" width="120px" align="left" />
        <mj-text font-size="22px" font-weight="700" padding-top="16px">Your order is on the way</mj-text>
        <mj-text>Hi {{first_name | default: "there"}}, package {{order_id}} shipped via {{carrier}}.</mj-text>
        <mj-button href="{{tracking_url}}">Track package</mj-button>
        <mj-text font-size="13px" color="#6b7280">If the button fails, copy: {{tracking_url}}</mj-text>
      </mj-column>
    </mj-section>
    <mj-section padding="16px">
      <mj-column>
        <mj-text font-size="12px" color="#6b7280" align="center">
          Acme Inc · 123 Main St · <a href="{{unsubscribe_url}}">Unsubscribe</a>
        </mj-text>
      </mj-column>
    </mj-section>
  </mj-body>
</mjml>
```

Token syntax above is an example. Copy the project's real filters (`| default`, `//`, Handlebars helpers).

---

## Bulletproof button (Outlook)

Pad the `<td>`, not a `<div>`. VML only if Outlook desktop is a named target.

```html
<table role="presentation" cellspacing="0" cellpadding="0" border="0">
  <tr>
    <td bgcolor="#2563eb" style="border-radius:6px;">
      <!--[if mso]>
      <v:roundrect xmlns:v="urn:schemas-microsoft-com:vml" href="https://example.com"
        style="height:44px;v-text-anchor:middle;width:200px;" arcsize="10%" fillcolor="#2563eb" stroke="f">
        <w:anchorlock/>
        <center style="color:#ffffff;font-family:Arial,sans-serif;font-size:16px;font-weight:bold;">
          Confirm email
        </center>
      </v:roundrect>
      <![endif]-->
      <!--[if !mso]><!-- -->
      <a href="https://example.com"
         style="display:inline-block;padding:12px 24px;font-family:Arial,sans-serif;font-size:16px;color:#ffffff;text-decoration:none;border-radius:6px;">
        Confirm email
      </a>
      <!--<![endif]-->
    </td>
  </tr>
</table>
```

---

## Plain text

```text
Subject: Your order is on the way

Hi Ada,

Package ORD-123 shipped via UPS.

Track: https://example.com/t/ORD-123

— Acme
Unsubscribe: https://example.com/unsub
```

Same facts as the HTML. "Please view this email in a browser" is not a plain-text part.

---

## Deliverability

- Subject ≤ ~60 characters; set preview/preheader text
- No fake `Re:` / `Fwd:`, no ALL CAPS subject, no `!!!`
- Image-only mail gets filtered — keep real text
- Marketing: identity, physical address, unsubscribe. Confirm legal requirements; do not certify them
- Escape user-controlled text (`&`, `<`, quotes) before interpolation

---

## Verify

1. HTML + text parts exist and agree
2. 320px width: no horizontal scroll
3. Dark mode: text still readable (see [references/clients.md](references/clients.md))
4. Every href is absolute `https:` or `mailto:`
5. Tokens have fallbacks; leftover `{{` / `<%` is a bug
6. Name the clients you actually opened. Everything else is unverified
