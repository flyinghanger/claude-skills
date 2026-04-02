---
name: image-to-svg
description: |
  Convert architecture diagrams, flowcharts, and other structured images (PNG/JPG) into clean, machine-readable SVG files. Use this skill whenever the user wants to: convert screenshots or images of diagrams into editable vector format; make diagram images parseable by programs; create SVG versions of architecture charts, flowcharts, or system diagrams; or replace raster images with text-based vector equivalents in Markdown files. Trigger on phrases like "convert image to SVG", "make this diagram editable", "turn this into vector", "make this parseable", or any request involving diagram images and programmatic readability.
---

# Image-to-SVG Conversion Skill

Convert raster images of architecture diagrams, flowcharts, and structured charts into clean, hand-crafted SVG files that are both visually faithful to the original and machine-parseable as XML.

## Why SVG for Diagrams

SVG is the ideal format for architecture diagrams because it serves two audiences simultaneously: humans see a rendered visual, and programs see structured XML with every node, label, and connection explicitly represented. Unlike Mermaid (which has poor layout control for complex diagrams) or raw PNG (which is opaque to programs), SVG gives you pixel-level layout precision with full text extractability.

## Core Workflow

1. **Read the source image** carefully, identifying all elements: boxes, labels, arrows, layers, groupings, color coding, and spatial relationships.
2. **Plan the SVG structure** by mapping visual layers to SVG groups, choosing coordinate systems, and defining reusable styles.
3. **Write the SVG by hand** using `<rect>`, `<text>`, `<line>`, `<path>`, and `<g>` elements. Do NOT use automated converters -- hand-authored SVG produces cleaner, more semantic output.
4. **Validate XML correctness** before delivering.
5. **Convert to PNG** if the target renderer doesn't support SVG.

## SVG Authoring Rules

### Font Handling (Critical)

Use `system-ui, -apple-system, sans-serif` as the font-family. This is the single most important rule for CJK (Chinese/Japanese/Korean) text rendering.

```xml
<svg xmlns="http://www.w3.org/2000/svg" font-family="system-ui, -apple-system, sans-serif">
```

The reason this works: `system-ui` maps to the OS's default UI font, which on macOS is PingFang SC (with full CJK support), on Windows is Microsoft YaHei, and on Linux desktops is typically Noto Sans CJK. These system fonts have comprehensive Unicode coverage including all CJK characters with proper bold/weight variants.

**Never change the font to fix rendering issues.** If Chinese text displays correctly in the user's browser but breaks in your local CLI tools (cairosvg, ImageMagick, etc.), the problem is the CLI tool's font environment, not the SVG. The SVG is correct -- leave it alone.

### XML Escaping (Critical)

SVG is XML. All XML special characters in text content must be escaped:

| Character | Escape | Common occurrence |
|-----------|--------|-------------------|
| `&` | `&amp;` | "A & B", "R&D" |
| `<` | `&lt;` | Comparisons |
| `>` | `&gt;` | Arrows in text |
| `"` | `&quot;` | Inside attributes |

The `&` character is the #1 cause of SVG load failures. If an SVG fails to load, check for unescaped `&` first -- this is almost always the root cause.

### Diagnostic Flowchart

When an SVG doesn't render correctly:

```
SVG won't load at all?
  -> Check XML validity: unescaped & is the most common cause
  -> Validate: python3 -c "import xml.etree.ElementTree as ET; ET.parse('file.svg')"

SVG loads but text shows as boxes/tofu?
  -> If it shows correctly in browser/Lark/Feishu but not in CLI tools:
     the SVG is CORRECT, the CLI tool lacks fonts. Do NOT change the SVG.
  -> If it shows incorrectly everywhere: check font-family is system-ui
```

### Structure and Style

Use CSS classes in a `<defs><style>` block for consistent styling:

```xml
<defs>
  <style>
    .box { rx: 4; ry: 4; stroke-width: 1; }
    .box-red { fill: #fce4ec; stroke: #e57373; }
    .label { font-size: 13px; font-weight: 600; fill: #333; }
    .arrow { fill: none; stroke: #999; stroke-width: 1.2; marker-end: url(#arrowhead); }
  </style>
  <marker id="arrowhead" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto">
    <path d="M0,0 L8,3 L0,6 Z" fill="#999"/>
  </marker>
</defs>
```

Use semantic grouping with `<g>` and comments to organize layers:

```xml
<!-- Layer: Frontend UI -->
<g transform="translate(140, 10)">
  <rect ... />
  <text ...>Frontend UI</text>
</g>
```

### Color Conventions

When the source image uses color coding (e.g., red = key focus, green = open source), preserve the color semantics with named CSS classes and include a legend in the SVG.

### Arrow Definitions

Define arrow markers once in `<defs>` and reuse via `marker-end`:

```xml
<!-- One-way arrow -->
<marker id="arrow" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto">
  <path d="M0,0 L8,3 L0,6 Z" fill="#999"/>
</marker>

<!-- Bidirectional: use both marker-start and marker-end -->
<line x1="100" y1="50" x2="300" y2="50"
      marker-start="url(#arrow-reverse)" marker-end="url(#arrow)"/>
```

## Converting SVG to PNG (When Needed)

If the target platform doesn't render SVG in Markdown, convert to PNG. Preferred tool chain:

1. **Playwright + headless Chrome** (best quality, full font support):
   ```python
   from playwright.async_api import async_playwright
   # Use device_scale_factor=2 for retina quality
   ```

2. **cairosvg** (fast, but needs CJK fonts installed):
   ```python
   import cairosvg
   cairosvg.svg2png(url='input.svg', write_to='output.png', scale=2)
   ```
   Requires `Droid Sans Fallback` or `Noto Sans CJK` font on the system, and you must change the SVG font-family to match the installed font name. Only change the font in a **temporary copy** for rendering -- never modify the canonical SVG.

3. **ImageMagick** (often fails with SVG XML parsing, not recommended).

## Updating Markdown References

When replacing image references in Markdown, use the standard image syntax:

```markdown
![Diagram description](filename.svg)
```

If the original used `.drawio` or `.png` references, replace them. Keep the original reference as an HTML comment for backup:

```markdown
<!-- ![Original](old_file.drawio) -->
![Diagram description](new_file.svg)
```

## Quality Checklist

Before delivering an SVG:

- [ ] All text content has XML special characters escaped (`&amp;` etc.)
- [ ] Font-family is `system-ui, -apple-system, sans-serif`
- [ ] XML validates: `python3 -c "import xml.etree.ElementTree as ET; ET.parse('file.svg')"`
- [ ] Spatial layout matches the source image (boxes, layers, groupings)
- [ ] All labels and text from the source are present
- [ ] Color coding is preserved with CSS classes
- [ ] Arrows have proper marker definitions
- [ ] Comments document the structure for future editors
