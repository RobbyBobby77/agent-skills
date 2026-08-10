# PptxGenJS — Creation Reference

## Text

```javascript
slide.addText("Title", {
  x: 0.5, y: 0.3, w: 9, h: 0.6,
  fontSize: 32, fontFace: "Arial", bold: true,
  color: "F8FAFC", margin: 0,
});

// Rich runs
slide.addText([
  { text: "Bold ", options: { bold: true } },
  { text: "and ", options: { italic: true } },
  { text: "accent", options: { color: "38BDF8", bold: true } },
], { x: 0.5, y: 1, w: 9, h: 0.4, fontSize: 16, color: "E2E8F0" });

// Bullets — NEVER type "•" yourself
slide.addText([
  { text: "First", options: { bullet: true, breakLine: true } },
  { text: "Second", options: { bullet: true, breakLine: true } },
  { text: "Nested", options: { bullet: true, indentLevel: 1, breakLine: true } },
  { text: "Numbered", options: { bullet: { type: "number" } } },
], { x: 0.5, y: 1.5, w: 4.5, h: 2.5, fontSize: 15, color: "E2E8F0" });
```

## Shapes

```javascript
slide.addShape(pres.ShapeType.rect, {
  x: 0.5, y: 1, w: 4, h: 2.5,
  fill: { color: "1E293B" },
  shadow: { type: "outer", color: "000000", blur: 8, offset: 3, angle: 135, opacity: 0.25 },
});

slide.addShape(pres.ShapeType.roundRect, {
  x: 5, y: 1, w: 4.5, h: 2.5,
  fill: { color: "1E293B" }, rectRadius: 0.12,
});

slide.addShape(pres.ShapeType.ellipse, {
  x: 0.5, y: 4, w: 0.4, h: 0.4,
  fill: { color: "38BDF8" },
});

slide.addShape(pres.ShapeType.line, {
  x: 0.5, y: 0.95, w: 9, h: 0,
  line: { color: "334155", width: 1.5 },
});
```

## Charts

```javascript
slide.addChart(pres.ChartType.bar, [{
  name: "Revenue",
  labels: ["Q1", "Q2", "Q3", "Q4"],
  values: [4.2, 5.1, 5.8, 6.4],
}], {
  x: 0.5, y: 1.1, w: 9, h: 4,
  barDir: "col",
  chartColors: ["38BDF8", "818CF8"],
  chartArea: { fill: { color: "0F172A" } },
  catAxisLabelColor: "94A3B8",
  valAxisLabelColor: "94A3B8",
  valGridLine: { color: "1E293B", size: 0.5 },
  catGridLine: { style: "none" },
  showValue: true,
  dataLabelColor: "E2E8F0",
  dataLabelPosition: "outEnd",
  showLegend: false,
  showTitle: false,
});

// LINE, PIE, DOUGHNUT, SCATTER, RADAR also available
slide.addChart(pres.ChartType.pie, [{
  name: "Share", labels: ["Product", "Services", "Other"], values: [55, 30, 15],
}], {
  x: 5.5, y: 1.2, w: 4, h: 3.5,
  chartColors: ["38BDF8", "34D399", "FBBF24"],
  showPercent: true,
  showLegend: true,
  legendPos: "b",
});
```

## Tables

```javascript
slide.addTable([
  [
    { text: "Metric", options: { bold: true, color: "F8FAFC", fill: { color: "1E293B" } } },
    { text: "Value", options: { bold: true, color: "F8FAFC", fill: { color: "1E293B" } } },
  ],
  ["NRR", "118%"],
  ["Churn", "2.1%"],
], {
  x: 0.5, y: 1.2, w: 9, colW: [4.5, 4.5],
  border: { pt: 0.5, color: "334155" },
  fontFace: "Arial", fontSize: 14, color: "E2E8F0",
  align: "left", valign: "middle",
});
```

## Images

```javascript
// Preserve aspect ratio — never invent both dimensions independently
const maxH = 3.0, ow = 1600, oh = 900;
const w = maxH * (ow / oh);
const x = (10 - w) / 2;
slide.addImage({ path: "chart.png", x, y: 1.5, w, h: maxH, altText: "Chart" });

// Cover / contain
slide.addImage({
  path: "photo.jpg", x: 0, y: 0, w: 5, h: 5.625,
  sizing: { type: "cover", w: 5, h: 5.625 },
});
```

## Icons (react-icons → PNG)

```javascript
const React = require("react");
const ReactDOMServer = require("react-dom/server");
const sharp = require("sharp");
const { FaRocket } = require("react-icons/fa");

async function iconPng(Icon, color = "#38BDF8", size = 256) {
  const svg = ReactDOMServer.renderToStaticMarkup(
    React.createElement(Icon, { color, size: String(size) })
  );
  const buf = await sharp(Buffer.from(svg)).png().toBuffer();
  return "data:image/png;base64," + buf.toString("base64");
}

const icon = await iconPng(FaRocket);
slide.addImage({ data: icon, x: 0.6, y: 1.3, w: 0.45, h: 0.45 });
```

Rasterize at ≥256px; display size is controlled by `w`/`h` in inches.

## Backgrounds

```javascript
slide.background = { color: "0F172A" };
// or image: slide.background = { path: "bg.jpg" };
```

## Slide masters (optional)

```javascript
pres.defineSlideMaster({
  title: "CONTENT",
  background: { color: "0F172A" },
  objects: [
    { placeholder: { options: { name: "title", type: "title", x: 0.5, y: 0.3, w: 9, h: 0.6 } } },
  ],
});
const s = pres.addSlide({ masterName: "CONTENT" });
s.addText("Hello", { placeholder: "title" });
```
