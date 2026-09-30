# Diagram style

Workflow maps should make sequence, branching, or handoffs easier to understand. Do not create a diagram for a one-step fact.

## Default SVG specification

- Canvas: approximately 620 × 390 pixels for technique maps; 680 × 520 pixels for the overall map.
- Background: `#f7fafc` with a modest corner radius.
- Main text: `#243746` in Arial or another widely available sans-serif font.
- Primary stroke: `#54778b`.
- Supporting fills: pale blue `#e8f1f5`, pale green `#edf6ef`, pale gold `#fff4df`.
- Accent strokes: green `#5b8465`, gold `#a97a24`.
- Title: centered, uppercase, 18 px, bold.
- Node text: 15–17 px with short phrases.
- Arrows: vertical `↓` characters or simple SVG paths, centered with generous spacing.
- Accessibility: every SVG must include `<title>` and `<desc>`.

## Content rules

- Use three to seven nodes.
- Start with the scientific input or qualification step.
- End with the decision, QC checkpoint, downstream assay, or customer outcome.
- Use a branch only when two paths materially change the discussion.
- Label a proposed or hypothetical workflow as `PROPOSED WORKING SEQUENCE`.
- Keep product names out of the map unless the product itself is the workflow stage.
- Never place long explanatory paragraphs inside a diagram.

## Markdown placement

Use a relative link:

```md
![Descriptive workflow map](Account_Topic_maps/overall_workflow.svg)
```

The scientific overview text and overall map may share a two-column Markdown table, but they remain separate cells. Technique questions, product fit, and the technique map use three separate cells. Do not merge them into one row-spanning graphic or use HTML layout.

## Notion fallback

When a destination cannot preserve local SVG links, create a separate `*_Notion_Copy.md` file. Put each workflow in its own fenced `text` block after the associated prose:

```text
starting material
        ↓
first transformation
        ↓
purification or QC
        ↓
downstream readout
```

Do not place prose in the text diagram. Do not use `<br>` tags to force vertical layout.
