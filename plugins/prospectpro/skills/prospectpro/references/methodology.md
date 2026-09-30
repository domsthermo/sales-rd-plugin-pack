# Analysis Methodology

Use this reference for workbook intake, technique/workflow inference, gap ranking, and value sizing.

## Workbook intake

For the standard Territory Invoice Report, treat `SGN` as the account identifier. A named-company request may intentionally roll up several related SGNs after fuzzy name matching, but preserve the exact included SGNs so the aggregation is auditable. An exact numeric or full SGN remains a single-account request. Do not use fuzzy matching to merge unrelated SGNs.

Inspect the workbook before analysis. Record:

- filename, sheet names, header rows, row counts, and date coverage;
- exact account/site identifiers and any roll-up fields;
- SKU, product description, product family/category, quantity, unit price, extended sales, freight, credits/returns, and net sales fields;
- currency, units, fiscal/calendar assumptions, filters, footers, subtotals, formulas, and hidden rows/columns that materially affect totals.

Use the narrowest defensible sales measure. If net sales exists, prefer it and separately retain freight/credits where available. If only extended sales exists, label it. Treat blanks as unknown unless the workbook definition makes them zero. Retain negative and zero-value rows unless a documented exclusion applies.

Reconcile:

1. raw fact-row total;
2. included analysis-row total;
3. excluded total with reason;
4. product-family totals back to the included total.

Use the maximum invoice date in the latest year as the YTD cutoff. Compare latest-year YTD net sales with the exact same inclusive prior-year period. Never compare a partial current year with a full prior year. If the workbook uses fiscal periods, preserve those instead of imposing calendar YTD.

## Product normalization

Preserve original SKU and description. Create a normalized family only from an authoritative catalog mapping, an unambiguous description, or explicit user context. Keep unmatched items as `Unmapped`; do not force them into a family.

Distinguish:

- consumables from instruments;
- accessory/maintenance items from assay reagents;
- one-time purchases from recurring usage;
- direct-customer purchases from distributor, incubator, parent, or site-level purchases;
- returns/credits from lack of demand.

## Evidence matrix

Build a private working matrix before writing recommendations:

| Claim | Workbook | Customer email | Public primary source | Publication | Label | Confidence |
| --- | --- | --- | --- | --- | --- | --- |
| [claim] | [sheet/rows or none] | [thread/date or none] | [link or none] | [DOI/link or none] | Known/Inferred/Assumed/Missing | High/Medium/Low |

Do not include weak evidence simply to fill every column.

## Technique and workflow inference

A **technique** is a scientific method or operational method within the biological R&D scope, for example flow cytometry, cell culture, qPCR, western blot, ELISA, imaging, transfection, genome editing, or nucleic-acid purification.

A **workflow** is an end-to-end application or development process, for example ADC development, cell-therapy development, immuno-oncology research, biomarker validation, recombinant protein production, or diagnostic assay development.

For each workflow, map:

`workflow stage -> technique -> evidence -> observed product family -> plausible adjacent category -> validation question`

Use publications to support what the scientists or company appear to do, not to prove where they buy each reagent. Use purchases to support observed commercial footprint, not to prove every scientific use.

## Gap qualification

A gap is reportable only when all three are present:

1. a credible workflow or technique need;
2. a relevant seller product category;
3. no observed purchase for that category in the exact workbook scope and period, or materially low attach/spend relative to an observed anchor.

Check for contradictions such as distributor purchasing, site mismatch, product-description ambiguity, recent returns, older purchases outside the period, or a likely competitor incumbent.

Use this prioritization score only to rank, never as a purchase probability:

| Factor | Points |
| --- | ---: |
| Workflow fit | 0-3 |
| Evidence strength | 0-3 |
| Purchase adjacency | 0-3 |
| Timing / recent trigger | 0-2 |
| Relationship signal | 0-2 |
| Contradiction or adoption risk | subtract 0-3 |

Interpretation:

- 9-13: high priority;
- 6-8: medium priority;
- 0-5: low priority or validation only.

Do not show the numeric score unless it helps the user. Always show the reason and confidence.

## Lapsed-product detection

Use normalization output to find win-back candidates, not to declare churn. The default mechanical candidate requires:

1. at least three distinct historical positive-purchase dates;
2. at least two historical intervals from which to estimate cadence;
3. no positive sales in the latest-year YTD comparison window; and
4. time since the last positive purchase greater than `max(90 days, 1.75 x the median historical interval)`.

Then review the candidate scientifically and commercially. Exclude or downgrade one-time instruments, service/maintenance, project-only buys, strongly seasonal items, returns without a true purchase pattern, site/account migration, replacements, and ambiguous product descriptions. Check PYTD, all historical positive sales, credit activity, relevant Outlook context, and public workflow continuity. A retained recommendation must be labeled as a lapsed or win-back opportunity and use recapture toward demonstrated historical revenue as its preferred value anchor.

## Value sizing

Choose the strongest available model.

### Unit-demand model

`annual experiments or batches x units per experiment or batch x expected realized unit price x attainable share`

### Attach-rate model

`annual anchor-category spend x adjacent-category attach-rate x attainable share`

Use attach rates only when supported by supplied peer/account data or clearly labeled directional assumptions.

### Run-rate model

`observed quantity during covered months / covered months x 12 x adjacent units per anchor unit x expected realized unit price x attainable share`

Adjust only when seasonality or a project ramp is evidenced.

### Installed-base model

`relevant instruments or users x annual consumable pull-through per instrument or user x attainable share`

Never infer installed base from a single consumable without labeling it as an assumption.

For each opportunity, calculate one private base-case annual estimate and carry only the rounded attainable seller-revenue figure into the report. Retain the formula, inputs, labels, confidence, and validation question in the working analysis so the number remains auditable.

Use the strongest customer-derived anchor available:

- current YTD annualized run rate;
- matching prior-year YTD run rate;
- recapture toward a demonstrated historical level;
- observed adjacent-category spend;
- customer-derived realized price and cadence.

Do not use a public list price as expected net revenue. Do not infer installed base from a single consumable. If the inputs cannot support a dollar estimate, write `TBD` or leave the report cell blank and identify the missing variable privately. Never force an estimate merely to fill the table.

## Product links

For every reported gap, find one to three specific official Thermo Fisher product or portfolio pages that match the workflow need. Prefer direct product pages and current portfolio pages over brochures, search results, or generic category homepages. Stay within biological R&D and exclude chemicals, chromatography, and mass spectrometry. A product link supports what to pitch; it does not prove the customer needs or will buy the product.

## Contact qualification

A contact is reportable only when both conditions are met:

1. the person's current employer and role are verified from a current authoritative company or institution page, a recent exact Outlook message, supplied customer data, or another reliable current source;
2. the person's responsibilities or demonstrated work connect directly to a priority workflow, whitespace opportunity, purchasing process, or active relationship.

Prefer scientific and technical workflow owners first, then relevant procurement, lab operations, or business contacts. Omit generic senior leaders whose connection to the opportunity is unclear. A paper, patent, poster, or conference listing can establish scientific relevance, but it cannot establish current employment unless a separate current source confirms the affiliation.

Use only verified email addresses from supplied data, authoritative public pages, or exact Outlook messages. Never generate an address from a company naming convention. Keep source links in the report's final `Sources` section and leave unknown contact fields blank.

After gap qualification, use `scripts/match_gaps_to_contacts.py` to rank explicit overlap between each gap and verified contacts. Workflow matches are strongest, followed by technique matches, relevant topic tags, technical or purchasing responsibility, and a known relationship. The input tags must come from evidence already reviewed; do not manufacture tags merely to create a match. Report no match when none qualifies, consolidate one person matched to several gaps, and preserve source ids for final citation.
