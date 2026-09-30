---
name: prospectpro-setup
description: Create or refresh a private reusable ProspectPro writing-style profile for one seller from their own sent external customer emails or pasted examples. Use when a user asks to set up, personalize, or refresh ProspectPro's email voice; do not use during ordinary account analysis.
---

# ProspectPro Writing Profile Setup

Create one compact `prospectpro-user-profile.md` file that the user can save in a private ChatGPT Project and reuse across future ProspectPro chats. This is a one-time onboarding workflow, not part of every account analysis.

## Evidence

Use either:

1. eight to fifteen messages sent by the mailbox owner directly to external customers or prospects; or
2. five to ten representative examples pasted or uploaded by the user.

When Outlook is available, search only the mailbox owner's Sent mail. Exclude internal recipients, forwards, automated notices, newsletters, calendar responses, legal templates, mass mail, messages dominated by quoted history, and ambiguous authorship. Fetch full bodies only for the selected small sample.

Never retain raw messages, recipient names, email addresses, customer names, confidential facts, signatures with personal contact details, or quoted customer text in the profile.

## Build the profile

Infer stable writing tendencies rather than copying phrases. Capture:

- typical greeting and opening style;
- sentence and paragraph length;
- level of warmth and directness;
- how evidence or account context is introduced;
- preferred call to action;
- closing and sign-off style;
- words, punctuation, and sales clichés the user tends to avoid;
- two short **invented** example patterns that contain no source-message wording or customer details;
- confidence and sample count.

Do not invent a preference when the evidence is mixed. Mark it `Unclear`.

Save a concise Markdown file named `prospectpro-user-profile.md` with:

```markdown
# ProspectPro User Writing Profile

Created: YYYY-MM-DD
Sample: [count] sent external messages | [or] user-provided examples

## Voice
- ...

## Structure
- ...

## Calls to action
- ...

## Avoid
- ...

## Safe invented patterns
- ...

## Usage rules
- Match this style only for outreach wording.
- Never import facts, people, companies, or claims from the examples.
- Current account evidence always controls factual content.
- Keep every draft unsent unless the user separately authorizes sending.
```

Give the file to the user and tell them to add it to the **Project Sources** of their private ProspectPro ChatGPT Project. Future ProspectPro chats should use that project source automatically.

Do not rescan email after creating the profile. Refresh it only when the user explicitly asks or replaces the file with a newer profile.
