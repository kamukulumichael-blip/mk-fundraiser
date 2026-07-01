# RAISR → Agent Sync Protocol

**What this is:** The weekly ritual for keeping Raisr and the LearnImpact Claude.ai agents in sync.
**When:** Every Monday, after research.py has run (check that alerts.json timestamp is today's date).
**Time required:** 5 minutes.

---

## THE MONDAY RITUAL (5 steps)

### Step 1 — Get this week's brief from Raisr
Open: https://kamukulumichael-blip.github.io/mk-fundraiser/
Unlock with passphrase → Command Center → Weekly Brief section.
Copy the `monday_brief_summary` text (or read it from raw JSON below).

Raw alerts.json (always current):
https://raw.githubusercontent.com/kamukulumichael-blip/mk-fundraiser/main/data/alerts.json

### Step 2 — Paste into Chief (or whichever agent you're starting with)
Open the LearnImpact Claude.ai Project → Chief agent.
Start your Monday session with this exact opener:

---
**MONDAY PIPELINE BRIEF — [DATE]**

[Paste the monday_brief_summary from alerts.json here]

**Hot this week:**
- [List the top 2–3 items from this_week_actions in alerts.json]

**Funding gap status:**
- SOMA confirmed: $[soma_confirmed_usd]
- SOMA needed: $[soma_needed_usd]
- Gap: $[calculated gap]
- Biggest pipeline bet: [top hot_list item]

**Any new conflicts or decisions since last week:**
- [Check DECISIONS_LOG.md for anything added this week]

---

### Step 3 — Upload DECISIONS_LOG.md if updated
If any new decisions were locked this week (in this repo or during any Claude.ai session),
upload the updated DECISIONS_LOG.md to /00_Shared/ in the Claude.ai Project.
Replace the previous version.

### Step 4 — If Pipeline needs to work this week
Paste relevant funder records from donors.json or funders.json directly into your message.
Pipeline is already briefed on strategy. It just needs the current relationship data.

Example: "Pipeline — Sandra at VTF. Here is her current CRM record: [paste donor record]"

### Step 5 — If a decision gets locked during the session
Any locked decision goes back to DECISIONS_LOG.md in this repo + /00_Shared/ in the Project.
Use the same format as existing decisions. Commit to repo. Upload to Project.

---

## WHAT AGENTS ALREADY KNOW (don't re-explain these)
- Direction C strategy (locked May 2026)
- SOMA/KiuFunza programme specs and locked cost figures
- Two-entity firewall (LearnImpact vs Timamu)
- All decisions in DECISIONS_LOG.md (if file is current in /00_Shared/)
- Michael's working style and approval requirements

## WHAT AGENTS NEED FROM YOU EACH WEEK (always paste these)
- `monday_brief_summary` — the week's intelligence in plain language
- Current `this_week_actions` list — the priority queue
- Any relationship-specific context for the funder/contact you're working on
- Any new locked decisions

## THE ANTI-PATTERN TO AVOID
Do NOT open a Pipeline or Chief session cold, without pasting Raisr context.
If you skip the Monday brief paste, agents will work from stale pipeline data.
Even a 3-sentence summary is better than nothing.

---

## WHAT RAISR DOES AUTOMATICALLY
- research.py runs every Monday 03:00 UTC (06:00 EAT) — no manual trigger needed
- alerts.json is updated with new intelligence, hot list, and monday_brief_summary
- Dashboard refreshes automatically when you open it

## WHAT STILL REQUIRES MANUAL ACTION
- Pasting context into Claude.ai agent sessions (agents can't read GitHub URLs)
- Uploading DECISIONS_LOG.md to /00_Shared/ when decisions change
- Adding relationship notes to donors.json after calls/meetings
- Confirming any CRM update via the Raisr interface (touchpoint log)

---

## PIPELINE SYSTEM PROMPT ADDITIONS
The following text should be appended to Pipeline's system prompt in the Claude.ai Project.
Add it under a new section titled "RAISR INTEGRATION":

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
RAISR INTEGRATION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Raisr is Michael's private fundraising intelligence hub (GitHub Pages static
site). It is the authoritative source for live pipeline state, funder records,
CRM data, and weekly AI-generated intelligence.

Raisr runs every Monday at 06:00 EAT and generates:
  • monday_brief_summary — week's state-of-play in 4-5 sentences
  • hot_list — top funder opportunities by composite score per programme
  • this_week_actions — prioritised action queue with deadlines
  • funding_gap — confirmed vs needed vs pipeline per programme
  • cross_programme_conflicts — funder appearing in multiple entity pipelines

Michael will paste the monday_brief_summary and this_week_actions at the start
of each Monday session. When he does, treat this as the authoritative pipeline
update for the week — not a supplement to your memory, a replacement of it.

The /00_Shared/ folder contains DECISIONS_LOG.md — the locked decision log
maintained in Raisr. If DECISIONS_LOG.md conflicts with your memory, the file
wins. State the conflict in one line and proceed on the file's version.

When Michael pastes funder or CRM records from Raisr's JSON files, treat them
as the current state. Your prior conversation memory about that funder's status
is superseded.

Monday Mode 3 scan: when Michael opens a Monday session with a pipeline brief,
run Mode 3 immediately — produce the structured Monday report (opportunities,
flags, recommended actions) anchored to the data just pasted. Do not wait to
be asked.
```
