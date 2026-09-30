# Report Format

Use this order. Omit empty optional content, but keep `Sources` last.

```md
# [Customer] Account Whitespace Brief

**Scope:** [account/site, latest YTD cutoff, currency, analyzed sales measure]

## Company Summary
[Two or three concise sentences covering scientific focus, platform or modality, stage, and current priorities.]

## Recent Developments
- **[Exact date]:** [one-line material development]

## Current Purchase Footprint
| Observed purchase area | [Latest year] YTD net sales | [Prior year] PY net sales | What it suggests |
| --- | ---: | ---: | --- |
| [Grouped purchase area] | [Net sales through cutoff] | [Net sales through the same prior-year cutoff] | [Techniques and workflows supported by the purchases] |

[Workbook citation]

## Techniques

![Customer technique map]([absolute path to customer-techniques.svg])

## Workflow Map

![Customer workflow map]([absolute path to customer-workflow-map.svg])

## Product Whitespace
| Priority | Gap | Why it fits | Estimated annual revenue if closed | Thermo Fisher products to pitch |
| ---: | --- | --- | ---: | --- |
| 1 | [Product category] | [Observed anchor] → [gap or low attach] → [product motion] | [Rounded annual attainable revenue or TBD] | [Direct official product links] |

[One sentence saying the estimates are directional annual opportunities based on purchase history and are not forecasts or confirmed customer budgets.]

## Outreach Draft

:::writing{variant="email" id="[unique five-digit id]" subject="[subject]" recipient="[verified email only]"}
[Personalized, user-style email. Lead with the customer's work or a relevant trigger, connect one or two high-confidence adjacencies to an outcome, and end with a low-friction CTA. Do not mention internal analysis, inferred spend, or private Outlook evidence.]
:::

## Key Contacts
| Contact | Current role / team | Matched gap(s) | Why relevant | Best outreach angle | Verified email |
| --- | --- | --- | --- | --- | --- |
| [Name] | [Current title or team] | [One or more retained gaps] | [Verified workflow, technique, purchasing, or relationship connection] | [One concise personalized angle] | [Verified email or blank] |

## Sources
- [Company / primary source — title, exact date](URL)
- [Paper — title, journal or repository, year, DOI/PubMed/publisher link](URL)
- [News source — title, exact date](URL)
- [Contact source — current company profile, team page, or other authoritative source](URL)
```

## Section rules

### Company and news

- Keep the company summary to two or three sentences.
- Use no more than three recent-development bullets, each one line with an exact date.
- Do not place source links inline. List company, news, trial, and paper sources only under `Sources`.

### Purchase footprint

- Use the workbook's latest invoice date as the YTD cutoff and compare the exact same inclusive prior-year period.
- Group products into useful workflow-oriented areas rather than listing every SKU.
- In `What it suggests`, name the techniques or workflows supported by those purchases.
- Put the workbook citation immediately after the table.
- Do not add total-net-sales, freight, reconciliation, exclusions, or data-quality detail below the table unless a material issue changes the conclusion.

### Product whitespace

- Keep `Why it fits` brief and use the causal shape `anchor present or increasing → gap or low attach → product motion`.
- A qualified lapsed-product row should use `historical recurring purchase → cadence now overdue → win-back motion`; call it lapsed or win-back, never confirmed churn.
- Link one to three specific official Thermo Fisher product or portfolio pages per gap. Do not link search results.
- Show one rounded annual attainable-revenue estimate. Use `TBD` or leave it blank when purchase history cannot support a credible estimate.
- Do not add a separate expansion-value, account-motion, Outlook-signals, evidence-posture, or confidence-and-gaps section.

### Key contacts

- Place this section immediately after the email writing block. `Sources` remains the final section.
- Include three to five contacts only when each person's current role is verified and directly relevant to a priority workflow, technical need, purchasing process, or existing relationship.
- Use the gap-to-contact matcher after gap qualification. Show the retained gap or gaps attached to each person; omit gaps with no credible contact instead of forcing a weak match.
- Prioritize technical or workflow owners and relevant procurement or operations contacts. Omit generic executives unless their role is directly material to the opportunity.
- Keep `Why relevant` and `Best outreach angle` to one concise phrase each.
- Include an email address only when it was supplied by the user or verified in an authoritative public source, the workbook, or an exact Outlook message. Never infer an email pattern. Leave the cell blank when unknown.
- Put public contact-source links under `Sources`, not inline in the table. A publication may support scientific relevance, but it does not by itself verify current employment.
- If no credible current contacts are verified, replace the table with `No current relevant contacts were verified.`

### Outreach and sources

- If the recipient address is not verified or supplied, omit the `recipient` attribute entirely.
- The email writing block must always have a subject and a unique five-digit id.
- Do not recommend a presentation or slide deck.
- `Sources` must be the final section. Do not put commentary, next steps, or caveats after it.
- Direct official Thermo Fisher links in the pitch column are the only inline public-link exception.
- Identify internal workbook and Outlook evidence by filename/sheet/date or thread/date, not as public sources.

## SVG requirements

Create two customer-specific SVG files in a writable task-owned output directory and embed them with absolute paths. Prefer the adaptive `scripts/render_svg_map.py` template described in [efficiency.md](efficiency.md); the template may use different lane counts, bubble counts, column counts, and explicit connections for each map.

### Technique map

- Show the scientific sequence in two or three readable lanes, such as build/express, purify/characterize, and test activity.
- Use a small legend to distinguish techniques observed in purchase history from techniques inferred from public science.
- Keep each node to a technique name and one concise purchase or method anchor.

### Workflow map

- Show the end-to-end application workflow from discovery through translation or the equivalent customer-specific stages.
- Within each stage, show key techniques and an observed purchase anchor.
- Add compact `Pitch / validate` callouts only where a supported whitespace opportunity exists.

Both SVGs must include accessible `<title>` and `<desc>` elements, high-contrast text, directional arrows, and a responsive `viewBox`. Avoid logos, decorative art, tiny text, dense legends, and clipped labels. Render or preview both files and correct overlap, clipping, or unreadable scaling before returning the report.
