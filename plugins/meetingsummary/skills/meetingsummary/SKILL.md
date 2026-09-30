---
name: meetingsummary
description: "Turn pasted or uploaded meeting notes into two copyable outputs: a concise structured meeting recap and an extremely short Salesforce opportunity update. Use after a customer, prospect, partner, or internal sales meeting when the user wants notes summarized for follow-up or CRM entry; do not update Salesforce or send messages."
---

# MeetingSummary

Convert the user's grounded meeting notes into a compact, seller-ready record. Use only the supplied notes or transcript unless the user explicitly asks for other sources. Never invent an attendee, role, commitment, opportunity stage, product, price, timeline, owner, or date.

## Intake

- Accept pasted notes, transcripts, rough bullets, or an uploaded note file.
- If the input clearly contains multiple meetings and the user did not ask to combine them, ask which meeting to summarize.
- If a detail is absent, write `Not provided`, `None confirmed`, or `TBD` as appropriate. Do not fill gaps from assumptions.
- Do not delay the output merely because the meeting date is absent. Use `DATE NOT PROVIDED` in the required Salesforce suffix.

## Produce exactly two copyable fields

Return only the two labels and writing blocks below. Do not add an introduction, analysis, confidence section, offer, or closing question.

When the host supports writing blocks, use two separate `standard` writing blocks with unique five-digit IDs. Put the labels outside the blocks so copied text contains only the intended content. If writing blocks are unavailable, use two separate fenced plain-text blocks.

### 1. Meeting Summary

Label the field `Meeting Summary`. Keep it concise, normally 120-220 words. Use this structure and omit a section only when it would add no value:

- `Meeting:` date and account/company, if provided
- `Attendees:` names plus roles/organizations when stated
- `Discussed:` the purpose and substantive topics in one compact paragraph or short bullets
- `Opportunity status:` what is happening commercially now, including interest, evaluation stage, stakeholder movement, buying process, timing, or blockers only when supported
- `Decisions:` confirmed decisions or `None confirmed`
- `Follow-up actions:` action — owner or `TBD` — due date or `TBD`
- `Open items / risks:` unresolved questions or blockers, if any

Prioritize who participated, what was discussed, decisions, opportunity movement, blockers, and concrete follow-up actions. Remove repetition, filler, greetings, and off-topic conversation while preserving useful scientific, technical, or commercial specifics.

### 2. Salesforce Update

Label the field `Salesforce Update`. Write exactly one or two short sentences, no bullets and usually no more than 45 words total. State:

1. where the opportunity stands and the most important customer need, signal, or blocker; and
2. the next action or decision point.

Do not claim a formal Salesforce stage unless the notes explicitly establish it. If the notes do not establish an opportunity, say so plainly. End the field with a space, hyphen, space, and the meeting date in `MM/DD/YYYY` format, for example ` - 09/30/2026`. If the date is missing, end exactly with ` - DATE NOT PROVIDED`. Nothing may appear after the date suffix.

## Quality check

Before responding, verify that there are exactly two copyable fields, every claim is grounded in the supplied notes, actions have owners and dates or `TBD`, the Salesforce field is one or two sentences, and its final characters are the required date suffix.
