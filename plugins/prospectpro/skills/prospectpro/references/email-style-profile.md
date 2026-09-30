# Outlook Writing-Style Profile

Use this reference before drafting outreach.

## Profile location

Prefer `${CODEX_HOME}/profiles/prospectpro-email-style.md` when `CODEX_HOME` is available and writable. Otherwise use `.codex/prospectpro/email-style-profile.md` in the current workspace. Create parent folders only as needed.

If the ProspectPro profile does not exist but a legacy `${CODEX_HOME}/profiles/account-whitespace-email-style.md` or `.codex/account-whitespace/email-style-profile.md` profile does, reuse its abstract style traits and save them at the ProspectPro location. Do not copy raw email content.

Never place raw messages, names, addresses, customer facts, or verbatim excerpts in the profile. Store only abstract writing traits and sampling metadata.

## When to build

Build the profile when no usable profile exists. Refresh it when the user explicitly asks to rerun, refresh, rebuild, or update the writing profile. Do not silently rebuild it on every account analysis.

## Qualifying messages

Use only emails that meet all of these rules:

- located in Sent mail or otherwise verified as sent by the mailbox owner;
- authored directly by the user, including user-authored replies after quoted history is removed;
- addressed to at least one external customer or prospect recipient;
- substantive enough to reveal writing style.

Exclude:

- internal-only messages and recipients at the user's employer domains;
- newsletters, automated notifications, calendar system messages, bounce notices, bulk marketing, and templates clearly written by someone else;
- forwarded text, quoted thread history, legal disclaimers, and signatures from the analyzed body;
- messages where authorship or customer-facing status is ambiguous.

Infer employer domains only when mailbox identity makes them clear. If internal/external classification is materially uncertain, exclude the message rather than guess.

## Sampling

Use 20-40 recent qualifying messages when available, spanning at least five external recipients and several purposes such as introductions, follow-ups, meeting asks, technical responses, and commercial check-ins. Search up to the prior 12 months by default. Paginate and deduplicate exact message IDs.

If fewer messages qualify, build a provisional profile and record the limitation. Never include a message merely to hit a sample count.

## Profile schema

Save only this abstract summary:

```md
# ProspectPro Email Style Profile

- Refreshed: YYYY-MM-DD
- Qualifying sample: [count]
- Date range: [start] to [end]
- Status: established | provisional
- Inclusion rule: sent by mailbox owner to external customers/prospects only

## Voice
- Formality:
- Warmth:
- Directness:
- Typical point of view:

## Structure
- Typical subject style:
- Opening pattern:
- Average body length:
- Paragraph / bullet preference:
- CTA pattern:
- Closing pattern:

## Language
- Common transition habits:
- Technical-detail level:
- Contraction preference:
- Punctuation / capitalization tendencies:
- Phrases or styles to avoid:

## Drafting rules
- [5-10 concise rules that recreate the style without copying old messages]
```

## Drafting behavior

Use the profile as a style constraint, not as factual evidence. Do not reuse distinctive sentences or customer-specific language from old emails. When the profile is provisional, keep the draft slightly more neutral and concise.

If Outlook access is absent or read-only, the analysis may still proceed. A read-only connector is sufficient for style profiling and account-thread review; creating an Outlook draft requires a separate write-capable action and explicit user request. Never send.
