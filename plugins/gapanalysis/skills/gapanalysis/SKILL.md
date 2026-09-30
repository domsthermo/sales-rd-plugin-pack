---
name: gapanalysis
description: Analyze a customer purchase-history spreadsheet for matched-period sales movement, gained business, lost or declining business, recurring-product lapses, purchase concentration, and evidence-backed product-category gaps. Use when the user supplies an .xlsx or .csv sales file and wants account gap analysis or whitespace analysis without charts, outreach, email, CRM changes, or complex commercial scoring.
---

# GapAnalysis

Turn a purchase-history spreadsheet into auditable tables and one concise report. Keep the work mechanical and evidence-led. Do not invoke ProspectPro or reuse its installed runtime.

## Boundaries

- Read spreadsheets and public sources only. Never access email, draft outreach, or change CRM records.
- Create no SVGs, charts, dashboards, opportunity scores, revenue forecasts, or contact recommendations.
- Preserve the source workbook. Write results to a separate output folder.
- State that an absent category was **not observed in the supplied purchase history for the matched account scope and period**. Never claim that the customer does not use or buy it.
- Leave unsupported values blank. Do not guess account matches, product mappings, research facts, or opportunity value.
- Treat exact numeric account or SGN input as one account. A company-name query may combine clearly related sites only when the script resolves them without ambiguity. If the script stops for ambiguity, show the candidate accounts and ask the user to choose.

## Required inputs

Require:

1. an `.xlsx`, `.xlsm`, or `.csv` purchase-history file;
2. a customer name or exact account/SGN when the file contains more than one customer.

The analyzer recognizes common purchase-history columns and the Thermo Fisher Territory Invoice Report fields, including `SGN`, `NSGN`, `Ship To`, `Invoice Date`, `SKU`, `Product Line Group`, `Pricing Product Line`, `Ship Quantity`, `Ext Sales`, and `Net Sales`.

## Workflow

### 1. Run the deterministic purchase analysis

Use a task-owned backend and output directory. Run:

```bash
python scripts/analyze_account.py PURCHASES.xlsx \
  --customer "CUSTOMER OR SGN" \
  --output-dir OUTPUT_DIR
```

Add `--sheet "SHEET NAME"` only when the workbook has multiple plausible data sheets. Add `--category-map mappings.csv` when the user supplies or confirms mappings for otherwise unmapped product families. The mapping CSV needs `match,category` columns.

The first run creates the report and tables using purchase evidence alone. It also writes `research-template.json` unless a research file was supplied.

### 2. Add one bounded public-research pass

Public research is expected unless the user opts out. Search the current company website and a small number of primary sources for active biological R&D workflows, platforms, modalities, and recent technical programs. Prefer official company pages, clinical-trial records, publications, patents, and conference abstracts. Use current sources for current claims.

Fill only supported fields in `research-template.json`:

- `company_summary`;
- `workflows[].id`, using one of the workflow ids in [workflow catalog](references/workflow-catalog.json);
- `workflows[].evidence`, a short factual description;
- `workflows[].source_title`, `source_url`, and `source_date`;
- `sources[]` for any additional source used in the summary.

Do not infer where the customer buys a reagent from a paper or company page. Research establishes workflow relevance; the spreadsheet establishes observed purchasing.

Rerun with:

```bash
python scripts/analyze_account.py PURCHASES.xlsx \
  --customer "CUSTOMER OR SGN" \
  --research OUTPUT_DIR/research-template.json \
  --output-dir OUTPUT_DIR
```

If research does not support a catalog workflow, do not add it. If the customer identity is uncertain, stop instead of researching the wrong organization.

### 3. Review only exceptions

Read the generated `gapanalysis-report.md` and `data-quality.csv`. Inspect the source workbook only when the script reports an ambiguous schema, account scope, reconciliation problem, or high unmapped sales.

If `unmapped-product-families.csv` contains material spend, show the rows to the user and ask for mapping help rather than forcing categories. A category mapping is a simple substring-to-category rule; preserve the raw product family and description in the detail tables.

### 4. Deliver

Return the report and the output folder. Summarize the largest matched-period change, the clearest lost or lapsed business, and the best-supported gaps. Keep the language factual and short.

The analyzer writes:

- `gapanalysis-report.md` — main report;
- `gapanalysis-summary.json` — machine-readable scope and metrics;
- `product-family-trends.csv` and `sku-trends.csv` — full matched-period comparisons;
- `gained-business.csv`, `lost-business.csv`, and `lapsed-business.csv` — focused movement tables;
- `gap-analysis.csv` — purchase/research gap candidates;
- `unmapped-product-families.csv` — mapping exceptions;
- `data-quality.csv` — scope, reconciliation, and parsing checks;
- `research-template.json` — structured research input when none was supplied.

## Analysis definitions

- **Latest YTD:** rows in the latest invoice year through the workbook's maximum invoice date.
- **Prior YTD:** the exact same inclusive calendar period one year earlier.
- **Gained business:** latest-YTD sales are positive and prior-YTD sales are zero or negative.
- **Lost business:** prior-YTD sales are positive and latest-YTD sales are zero or negative.
- **Declining business:** both periods are positive and latest-YTD sales are lower.
- **Lapsed candidate:** a recurring positive-purchase pattern with at least three distinct purchase dates, no positive latest-YTD sales, and time since last purchase greater than the larger of 90 days or 1.75 times historical median cadence. This is a win-back hypothesis, not confirmed churn.
- **Gap:** a catalog category linked to an observed purchase anchor, supported public workflow, or both, but not observed in the matched account scope and period.

Do not total gap rows as a pipeline estimate. They can overlap and contain no assumed opportunity value.
