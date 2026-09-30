# ProspectPro Plugin

ProspectPro is a skills-only plugin for biological R&D account development. Version 1.3.1 uses a short evidence-to-report pipeline: code handles the workbook, footprint, win-back evidence language, maps, product links, contact matching, caching, and rendering; the model updates one existing decision template with only the scientific and commercial judgments that cannot be derived safely. Exact numeric or full SGN requests remain single-account analyses.

## Requirements

- ChatGPT Work or Codex with plugin support.
- A customer purchase-history `.xlsx` file supplied in the task.
- Web research access.
- Outlook access when email context or a personalized writing-style profile is desired. Outlook is not bundled with this plugin and must be available and authenticated separately.

## Use

Start a new task after installation and ask:

> Use ProspectPro to analyze [customer] using this purchase-history workbook.

ProspectPro is read-only with respect to email and CRM systems. It drafts outreach but does not send email or change CRM records.

The first run builds private workbook and research caches. Later runs reuse stable evidence while refreshing time-sensitive news and trial information. A saved user profile supplies writing style without rescanning email.

## Version 1.3.1 performance design

- The model reads a compact decision pack rather than the full internal account pack.
- Public research is bundled into one discovery batch and one verification batch.
- Outlook is exact-first and optional for account evidence.
- The model writes only gaps, contacts, recent developments, and outreach.
- Purchase tables, maps, product links, contact matching, and report layout are generated automatically.
- The legacy full account specification remains accepted only for backward compatibility.

Version 1.3.1 strengthens that protocol without limiting the number of supported gaps, contacts, or win-backs. The model must update the existing decision template once, while the deterministic map framework is authoritative and requires no raster-preview troubleshooting.

Each rep can run **Set up my reusable ProspectPro writing style** once, then add the generated `prospectpro-user-profile.md` file to a private ChatGPT Project's Sources. Ordinary account runs reuse that profile without rescanning email.

## Installation and distribution

The plugin uses the portable Agent Plugins layout and also includes the Codex compatibility manifest. For local testing, add the plugin to a personal or repository marketplace and install it from the ChatGPT desktop Plugins Directory. For ChatGPT web distribution, publish it to an authorized workspace or submit it to the universal Plugins Directory.
