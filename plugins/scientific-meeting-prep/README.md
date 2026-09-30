# premeetingprep

premeetingprep is a private, skills-only plugin that turns a customer meeting into a source-grounded technical brief. It is designed for scientific sellers who need the actual meeting context, the relevant correspondence, the science, and a credible product-fit conversation in one artifact.

## What it does

- identifies the correct upcoming or named customer meeting from Calendar;
- retrieves the relevant email thread and reads full messages rather than relying on search snippets;
- researches the customer science using primary sources;
- maps official product capabilities to the customer's workflow without inventing fit;
- creates a complete Markdown meeting brief and standalone workflow diagrams;
- keeps verified facts, hypotheses, recommendations, and unknowns clearly separated;
- avoids raw HTML and `<br>` formatting that breaks in Markdown and Notion.

## Example prompts

- `Prepare a technical brief for my next customer meeting.`
- `Find my upcoming vaccine-development meeting and use the email thread for context.`
- `Turn this invitation into a scientific meeting brief.`
- `Update the brief after the customer sent this new protocol.`
- `Make the output compact because the meeting starts in 30 minutes.`

## Output

The default artifact is:

```text
outputs/<account>_<topic>_Technical_Meeting_Brief.md
outputs/<account>_<topic>_maps/
    overall_workflow.svg
    <technique>.svg
```

The brief includes the meeting objective, immediate read, opening, duration-matched agenda, scientific overview, technical questions, product fit, workflow maps, suggested close, commitments, and confidence gaps.

## Connections

This package does not contain customer data, passwords, or fixed service credentials. It uses whichever authorized Calendar, Email, Knowledge, CRM, and web-research capabilities are already available in the workspace. Calendar is required only when the plugin must discover or verify a meeting; a pasted invitation can serve as the fallback.
