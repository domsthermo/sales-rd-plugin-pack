# ProspectPro Performance and Recovery

Read this only when diagnosing performance, handling an unsupported workbook, inspecting cache behavior, or recovering an interrupted account-pack run.

## Performance target

ProspectPro has one deep-dive mode. Version 1.3.1 minimizes model orchestration by exposing a compact decision pack and generating report structure deterministically.

For a normal account, target:

- one `prepare` command;
- one web discovery batch and one batched open;
- one Outlook discovery batch and at most one message-fetch batch;
- one Update File patch to the existing decisions template;
- one `finalize` command.

An exception research batch is allowed only when a missing fact could change a material claim, retained gap, or current contact. Do not keep searching merely to collect more sources.

## What the account-pack pipeline owns

`scripts/run_account_pack.py prepare` performs:

- fuzzy company-name resolution against SGN, with exact numeric/full-SGN override;
- strict standard-report normalization;
- workbook fingerprint/cache lookup;
- matched YTD/prior-year periods and reconciliation;
- operational-charge exclusion;
- product-family rollups and lapsed-candidate surfacing;
- product-library initialization;
- research-cache freshness checks;
- timing-state creation;
- generation of a compact decision pack and decisions template.

`scripts/run_account_pack.py finalize` expands compact decisions and performs:

- all product-library queries in one process;
- gap-to-contact matching;
- adaptive SVG rendering and deterministic structural/layout QA;
- report rendering;
- research-cache refresh;
- runtime counter capture and history finalization.

Do not open the full account pack, inspect the product library, construct the legacy full account specification, reread the completed report, or create a map-preview workflow during a normal run. Do not replace these stages with repeated ad hoc snippets unless the pipeline reports a concrete unsupported condition.

## Orchestration budget

The only model-authored state in a normal run is one update to the `decisions.json` file created by `prepare`. Never delete and recreate it or produce a second JSON file. It contains company summary, developments, selected lapsed SKU strings, supported gaps, verified contacts, outreach, sources, and small operational counters. It must not contain footprint rows, SVG specifications, product-link results, matched-contact tables, or report layout.

The agent reads `decision-pack.json`, not `account-pack.json`. Inspect the internal pack only to resolve a reported warning, reconciliation problem, or unsupported schema. Do not impose an arbitrary count on credible gaps, contacts, or win-backs.

## Research cache

The cache is private operational state under `BACKEND/research-cache`. Its filename is a hash of the verified domain or sorted exact matched-SGN set, not a customer label.

- Core identity/science is reusable for 90 days.
- Current contact roles are reusable for 30 days.
- News and clinical-trial status must be checked live every run.
- Dynamic items may be stored as last-seen history but are never treated as current without a fresh check.
- A cached fact loses to newer primary evidence.

## Outlook efficiency

Start with exact domain filters in both directions. Search exact known contacts or project terms in the same discovery batch. When those searches are empty, record the empty result and stop.

Avoid broad company-name mailbox searches because purchase-report attachments and internal summaries create false positives. Before returning connector data to the model, map results to only the fields needed to decide relevance. Full message bodies should be fetched by exact id in one batch after selection.

## Web efficiency

The discovery batch should cover four intents at once:

1. official company identity, science, and pipeline;
2. developments in the last 12 months;
3. current team and workflow owners;
4. trials, papers, posters, patents, or protocols exposing methods.

Deduplicate URLs, prefer pages supporting several related facts, and open the selected pages together. Do not separately search every candidate contact, every SKU, or every wording variation after the authoritative page settles the fact.

## Standard Territory Invoice Report

The strict required columns are:

| Canonical use | Exact column |
|---|---|
| Customer filter and account identity | `SGN` |
| Parent / roll-up identity check | `NSGN` |
| Ship-to detail check | `Ship To` |
| Date | `Invoice Date` |
| Product | `SKU` |
| Product rollup | `Pricing Product Line` |
| Quantity | `Ship Quantity` |
| Revenue | `Net Sales` |

For a company-name request, compare the normalized name portion of every SGN and include all related SGNs that clear the fuzzy-match threshold. Preserve the exact matched SGN list in the pack. An exact numeric SGN or exact full SGN selects only that identifier. Reject short generic terms and unsafe broad matches.

`Sales Invoice #` is diagnostic only. Do not substitute Bill To, Order Date, Ship Date, Ext Sales, or another product hierarchy. If the standard signature is present but a required column is missing or renamed, stop and report the mismatch.

For a genuinely different workbook, run the generic detector. Create a small explicit column-map JSON only when a required field is missing or ambiguous.

## Timing integrity

`prepare` starts timing and records intake/workbook internally. `finalize` records product links, contacts, SVG, and report internally and closes the run.

The agent must time live company research, science research, Outlook, and gap analysis around the actual work. Do not start and immediately stop a phase after the work has already happened. Phase timing can overlap only when operations genuinely run concurrently.

Performance history contains durations and allowlisted counters only. It must never contain customer names, contacts, email content, URLs from correspondence, or purchase rows.

## Interrupted runs

If `prepare` succeeds but the run stops before `finalize`, inspect `BACKEND/current-run.json`.

- Stop only phases that are genuinely still active.
- Reuse the prepared account pack if the workbook fingerprint and exact matched-SGN set are unchanged.
- Re-run live news/trial checks if the interrupted run crosses into another day.
- Do not fabricate phase timing to make the history complete.

## Product links and SVGs

The verified link library remains the first lookup. Browse only when a retained gap has no suitable fresh match. The library excludes chemicals, chromatography, and mass spectrometry.

The adaptive SVG renderer owns lane sizing, wrapping, subtitle truncation, node positioning, and collision prevention. Finalization validates every node and link before rendering and returns `svg_qa: passed`. That deterministic result is authoritative: never rasterize, screenshot, open, or troubleshoot the SVGs during a normal run. If structural validation fails, report the concrete generator error instead of constructing an ad hoc preview system.
