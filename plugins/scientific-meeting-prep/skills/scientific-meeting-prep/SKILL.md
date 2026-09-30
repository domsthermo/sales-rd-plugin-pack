---
name: scientific-meeting-prep
description: Prepare an evidence-grounded scientific or technical seller meeting brief from a named or upcoming customer meeting, Calendar invite, email thread, pasted context, or existing brief. Use for life-science R&D, biotechnology, pharmaceutical, analytical, clinical, or laboratory customer meetings when the user wants meeting research, scientific workflow mapping, technical questions, product fit, a Markdown cheat sheet, or workflow diagrams. Do not use for generic company research without an upcoming meeting, completed-call follow-up, CRM writes, or sending customer communication.
---

# Scientific meeting prep

Create a turnkey seller brief that lets the user enter a technical customer meeting understanding the science, the customer's actual question, the relevant workflow, the product-fit boundaries, and the concrete next step to earn.

This skill is read-first and evidence-led. Never let a plausible scientific narrative outrun the Calendar invite, full email thread, supplied files, official product documentation, or current primary research.

## Load the supporting references

Read these files before producing a brief:

1. [Research and evidence rules](references/research-and-evidence.md)
2. [Brief template](references/brief-template.md)
3. [Diagram style](references/diagram-style.md)

## Supported requests

- **Named meeting:** The user gives an account, attendee, topic, invitation, or event link.
- **Next meeting:** The user asks for the next upcoming technical customer meeting.
- **Date view:** The user asks for a meeting on a specified day.
- **Pasted context:** The user supplies an invitation, email thread, protocol, abstract, or notes.
- **Brief update:** The user asks to revise an existing scientific meeting brief with new evidence.
- **Urgent prep:** The meeting is near; produce the concise usable artifact before doing optional enrichment.

## 1. Lock the target before researching

Treat the most recent explicit meeting, account, attendee, topic, or date as controlling. Never pivot to a different customer because another file or earlier conversation is nearby.

When the user names the meeting, account, attendee, or topic, use that target directly. When the user asks for the next meeting, search Calendar for the next three business days with no more than 25 results. Keep only future external meetings with a credible scientific, technical, R&D, laboratory, or product-development purpose.

- If exactly one meeting qualifies, select it and read the complete event.
- If several credible meetings remain, ask the user to choose from at most three.
- Do not search email, research the account, or start drafting until the target is unambiguous.
- When a direct Calendar event is available, use it as the authority for title, time, attendees, organizer, attendance status, location, meeting link, and agenda.
- When no Calendar event can be read, continue from a pasted invitation or user-supplied identity and label it: `User-supplied meeting identity; not Calendar-verified`.

## 2. Recover the real conversation

Search Email only after the meeting is locked. Use the account, named attendees, organizer, subject, and technical terms from the invite. Search subject variants and the customer's exact wording. Prefer a narrow, high-recall sequence over one broad query.

Read the full bodies of the relevant messages. Search snippets are discovery aids, not evidence. Reconstruct the thread in chronological order and capture:

- the customer's exact technical question;
- what Thermo Fisher or another seller already recommended;
- what the customer accepted, rejected, or asked to discuss;
- quantities, catalog numbers, workflows, buffers, instruments, matrices, timelines, and success criteria explicitly stated;
- people brought in for technical ownership and why;
- adjacent account signals that may matter, labeled as related but unconfirmed when linkage is not proven.

Do not claim an email search was empty, a message said something, or a relationship exists unless the completed source action supports it.

## 3. Build the evidence stack

Use sources in this order:

1. Calendar event for meeting identity and logistics.
2. Full customer and internal email messages for questions, commitments, and current context.
3. Supplied protocols, papers, decks, notes, and prior briefs.
4. CRM or account records for opportunity and relationship truth when available and material.
5. Official customer sources for the company, program, pipeline, and published work.
6. Peer-reviewed papers, trial registries, patents, and authoritative scientific sources.
7. Official Thermo Fisher product pages, manuals, application notes, and handbooks for product capabilities and limits.

Use current web research for facts that may have changed. For technical claims, prefer primary sources and official documentation. Link material claims to the direct source.

Classify every material statement as one of:

- **Verified:** directly supported by a source.
- **Customer-stated:** directly stated by the customer but not independently validated.
- **Inferred:** a scientifically reasonable interpretation that is not yet confirmed.
- **Unknown:** missing information that must be asked in the meeting.

Never turn a related purchase, another team's project, a product's general capability, or a literature precedent into a confirmed fit for the target workflow.

## 4. Translate the science into a seller conversation

First reconstruct the customer's end-to-end workflow. Then identify:

- the decision the customer is trying to make;
- the scientific bottleneck;
- the sample, matrix, analyte, organism, cell type, or construct;
- inputs, outputs, and handoffs between techniques;
- failure modes and sources of variability;
- required controls and acceptance criteria;
- current internal versus outsourced ownership;
- the smallest credible next experiment, evaluation, or specialist follow-up.

Map products to those workflow steps. For each product or service, state:

- what it does in plain language;
- why it may fit this specific workflow;
- the condition that must be true for the fit to hold;
- the technical question that qualifies it;
- any specification, compatibility, intended-use, scale, recovery, or validation boundary that prevents overpromising.

If no specific product is defensible, say that the current best fit is a design review or specialist consultation. Do not fill space with a catalog list.

## 5. Produce the artifact

When the user requests a Markdown brief or a file is clearly useful, create:

```text
outputs/<Account>_<Topic>_Technical_Meeting_Brief.md
outputs/<Account>_<Topic>_maps/
```

Use safe filename characters and preserve an existing brief only when the user explicitly asks to update it. Otherwise create a new file.

Follow the [brief template](references/brief-template.md), adapting its depth to the meeting. A 30-minute meeting should be scannable in roughly five minutes. Put the most useful seller content first:

1. meeting identity and objective;
2. recommended posture;
3. what is already known versus what must be decided;
4. best opening;
5. duration-matched agenda;
6. scientific overview and overall workflow map;
7. general questions;
8. technique sections;
9. if-they-say-X guidance when useful;
10. proposed pilot or next-step structure;
11. recommended close and commitments;
12. confidence, evidence limits, and source links.

For each major technique, use three clearly separated columns:

| Technique-specific questions | Thermo Fisher products and fit | Technique map |
|---|---|---|
| Probing questions and why each matters | Plain-language function, fit, conditions, and limits | One standalone diagram image |

Keep science prose, questions, and product fit as normal Markdown text. Put diagram content only in the diagram column. Do not turn the science summary or product fit into ASCII art.

## 6. Diagram and portability rules

Follow [diagram style](references/diagram-style.md).

- Make one overall workflow map and one map for each technique where a diagram materially improves understanding.
- Keep each diagram independent; never merge the science summary and diagram into a shared graphic.
- Place the overall workflow map to the right of the scientific overview in a two-column Markdown table.
- Place each technique map in its own third column beside, not inside, the question and product-fit prose.
- Default to clean standalone SVGs with a light background, dark blue-gray text, restrained teal/green/gold accents, vertical arrows, and short node labels.
- Use relative image paths so the folder stays portable.
- Do not use raw HTML, `<br>`, `<div>`, inline CSS, or HTML tables in the Markdown.
- Do not use escaped line-break artifacts or visible formatting markers.
- If the destination cannot preserve local images, also create a `*_Notion_Copy.md` variant using compact plain-text workflow blocks outside tables. Do not degrade the primary brief unless the user asks.

## 7. Urgent mode

When the meeting starts within one hour or the user says the prep is urgent:

- create and verify the core Markdown artifact first;
- prioritize the Calendar event and exact email thread;
- research only the science and official product facts needed to answer the customer's stated question;
- keep the agenda, top questions, opening, and close above optional background;
- leave unsupported fields blank or mark them unknown;
- do not delay delivery for optional CRM, broad company history, or decorative work.

## 8. Verification before handoff

Before claiming completion:

- confirm the Markdown file exists and has meaningful content;
- confirm every referenced diagram exists;
- search the Markdown for raw HTML markers, `<br>`, placeholder tokens, the wrong customer, and stale dates;
- confirm the target meeting, date, attendees, and technical topic match the evidence;
- confirm source links point to the actual event, message, paper, or official product page;
- confirm verified facts, inferences, related-but-unconfirmed signals, and unknowns remain distinguishable;
- open the finished file for the user when the host supports it.

Return the exact file link, the meeting time, the one-sentence technical read, and any material limitation. Do not claim that a connector, write, or file creation succeeded without verification.

## Boundaries

- This skill is read-only with respect to Calendar, Email, CRM, messaging, customer systems, and shopping carts.
- Never send messages, modify events, create CRM records, order products, or attach files without a separate explicit request and the applicable approval workflow.
- Do not expose private email contents in public research or package customer-specific data inside the plugin.
- Do not reuse one customer's brief as another customer's facts. Reuse only the format and reasoning pattern.
