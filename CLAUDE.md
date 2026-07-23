# CLAUDE.md — Raisr · LearnImpact Fundraising Intelligence Hub

## WHAT THIS TOOL IS
Raisr is Michael Kamukulu's private AI-powered fundraising intelligence hub.
Live: https://kamukulumichael-blip.github.io/mk-fundraiser/
Repo: https://github.com/kamukulumichael-blip/mk-fundraiser
Architecture: GitHub Pages static site + GitHub Actions cron (Monday 03:00 UTC) + Claude API in-browser + data/ JSON files.

**Two separate legal entities — always treat separately:**
- **LearnImpact** (ED: Michael Kamukulu) — SOMA + KiuFunza programmes
- **Timamu Foundation** (Founder: Michael Kamukulu) — disability inclusion + creator economy

---

## LEARNIMPACT — PROGRAMMES

### SOMA (top fundraising priority)
**Board-revised July 2026 — four components:**
1. Student Assessments (3x per year) + ability grouping for differentiated instruction
2. Live Learning Progress Data Dashboard — democratised, accessible to teachers, schools, government
3. Mwalimu Kinara (teacher recognition) — co-financed by local government
4. AI Predictive Analytics — using KiuFunza + Uwezo historical data to anticipate learning gaps
**DROPPED from programme: TaRL prescription · Mwalimu WhatsApp AI Bot**
- USD 3.12/student/year [LOCKED — do not re-derive] · USD 12/LAYS modelled (Mtwara RCT verifies 2027)
- Kibaha pilot: Term 3 2026, 10 schools · Mtwara RCT: 2027, 70 schools
- Government co-financing: Kibaha District Council (proves integration appetite)
- 2027 funding gap: USD 637K (USD 229K confirmed vs USD 866K needed)
- Pipeline: Founders Pledge $5M in review (Lorcan Clarke), VTF SOMA not started, Dovetail Track 2 not started
- NOTE: Founders Pledge DD round 2 may ask about programme model — need to brief Lorcan on redesign

### KiuFunza
- Teacher performance pay, Grades 1–7. 265 schools, 10 regions Tanzania.
- QJE-published: +9.4pp treatment effect. USD 7/child/year.
- Active funders: Hempel Foundation (Rosa, anchor USD 587K, Hearing Committee live), VTF (Sandra Oswald, TZS 462M ~USD 178K, signing imminent July 2026), Dovetail/Prevail Fund (Ali Ellegard, USD 100K Track 1 won)
- **CRITICAL: Never lead with Twaweza history. GoT sensitivity — frame as LearnImpact's independently verified programme.**

---

## TIMAMU FOUNDATION — SEPARATE ENTITY
- Persons with disabilities + creator economy + assistive technology
- 9–10M Tanzanians with disabilities · Tanzania Vision 2050: TZS 2B creator fund July 2026
- **CRITICAL: Never reference LearnImpact as implementing entity for Timamu proposals**
- Active: Microsoft AI for Accessibility ($150K rolling), Adobe Foundation ($50K rolling), Tanzania creator economy fund

---

## ACTIVE PIPELINE (as of 2026-07-01)

| Opportunity | Programme | Stage | Amount | Contact |
|---|---|---|---|---|
| Founders Pledge SOMA | SOMA | In Review | $5M | Lorcan Clarke |
| VTF KiuFunza Phase 5 | KiuFunza | Signing Imminent | $178K | Sandra Oswald |
| Hempel KiuFunza Renewal | KiuFunza | In Review (Hearing Committee) | $587K | Rosa |
| Dovetail Track 1 | KiuFunza | SIGNED July 2026 | $100K | Ali Ellegard |
| Dovetail Track 2 SOMA | SOMA | Identified (not started) | $150K | Ali Ellegard — pitch: AI analytics + dashboard |
| VTF SOMA | SOMA | Identified (not started) | $150K | Sandra Oswald |
| GPE Tanzania SOMA | SOMA | Identified | $500K | — |
| Microsoft AI Accessibility | Timamu | Identified | $150K | — |
| Adobe Foundation | Timamu | Identified | $50K | — |

---

## KEY CONTACTS / CRM

| Contact | Organisation | Role | Health | Next Action |
|---|---|---|---|---|
| Sandra Oswald | Vodacom Foundation | Manager | 🔴 HOT | Confirm signing date by 2026-07-10 |
| Rosa | Hempel Foundation | Programme Officer | 🟡 WARM | Await Hearing Committee — do not push |
| Lorcan Clarke | Founders Pledge | Applied Researcher | 🟡 WARM | Follow up if no word by 2026-08-15 |
| Vadim | Founders Pledge | FP Member (HNW) | 🟡 WARM | Lorcan to orchestrate — do NOT contact directly |
| Ali Ellegard | Dovetail/Prevail Fund | Programme Officer | 🟡 WARM | Start Track 2 SOMA conversation after Sep 2026 |
| Youdi Schipper | External Advisor | KiuFunza Research Advisor | 🟡 WARM | KF Update Call July 13 + 27. KiuFunza lane ONLY. |

---

## INTELLIGENCE RULES

### Cross-programme conflicts
VTF, Mastercard, FCDO, Google.org appear in both LearnImpact + Timamu pools.
Rule: always decide priority entity before approaching. Never allow simultaneous asks to same contact.

### Evidence to use
- "SOMA: USD 3.12 per student per year — less than the cost of a school exercise book"
- "KiuFunza: +9.4 percentage points treatment effect, published Quarterly Journal of Economics"
- "LAYS: USD 12 per Learning-Adjusted Year of Schooling (modelled — Mtwara RCT verifies 2027)"
- "Scale: Tanzania → Zanzibar → Burundi → East Africa. Prove → Partner → Embed → Replicate."
- "Timamu: 9–10M Tanzanians with disabilities. TZS 2B creator economy fund July 2026."

### Voice / tone
Michael's fundraising voice: direct, evidence-led, warm but not over-familiar, no jargon.
Never mention Twaweza in KiuFunza proposals or cold outreach.
Never position LearnImpact as Timamu's implementing entity.

---

## DATA FILES
- `data/funders.json` — 38+ funders with tier, status, alignment score, probability
- `data/opportunities.json` — active pipeline (10 opportunities)
- `data/donors.json` — CRM / relationship records (6 contacts)
- `data/alerts.json` — weekly AI-generated intelligence (regenerated every Monday)
- `data/sources.json` — 10 registered intelligence sources (Devex, FCDO, GPE, etc.)
- `data/events.json` — 5 upcoming conferences (UNGA Sep, APF Oct, GES Nov, etc.)
- `data/prospects.json` — staging layer for Quick Capture prospects

Live data readable at:
`https://raw.githubusercontent.com/kamukulumichael-blip/mk-fundraiser/main/data/alerts.json`

---

## WORKFLOW WITH CLAUDE AGENTS

### Starting any fundraising conversation
Paste the `monday_brief_summary` from alerts.json — it's the 4-5 sentence weekly state-of-play.
For specific funder work, paste the relevant record from funders.json or donors.json.

### For proposals / documents
Use the Document Studio in Raisr (it calls Claude directly with funder context pre-filled).
For complex proposals, bring the SOMA Concept Note v3 from Google Drive as context.

### Approval protocol
Diagnose → propose → Michael approves → build → Michael tests → push.
Do NOT push live changes to GitHub without Michael's review.

### Document save location (Google Drive)
- LearnImpact proposals: `LearnImpact/05_Fundraising/SOMA/` or `/KiuFunza/`
- Timamu proposals: `Timamu Foundation/02 - Resource Mobilisation/`

---

## STRATEGIC CONTEXT
LearnImpact is newly independent from Twaweza (May 2026).
Direction C (3-year strategy) requires board ratification via 2026 KiuFunza Stakeholder Survey results.
5-Year architecture: Prove → Partner → Embed → Replicate (Tanzania → Zanzibar → Burundi → East Africa).
USD 8.2M portfolio target 2027–2030.
SOMA is the pivot from KiuFunza — government integration is the endgame, not perpetual donor dependence.

---

## LOCKED DECISIONS (as of 2026-07-01)

**Google.org:**
- LearnImpact/SOMA leads. Timamu deferred until (a) LI relationship established AND (b) Timamu is registered.
- NOT in the cross-programme conflict list — decision is made.
- Two tracks: Track 1 = Google for Nonprofits (ad credits, rolling, immediate); Track 2 = Impact Challenge (competitive, relationship-first).

**LearnImpact registration:**
- Fully registered: Reg. 00NGO/R/8931 (Ministry certificate in hand).
- Timamu Foundation: NOT yet registered. Hard prerequisite before any Timamu application to Google, Microsoft, or any funder requiring legal entity.

**LearnImpact framing (non-negotiable):**
- NOT a startup. Never use startup language.
- Correct framing: "Established NGO, 10+ years KiuFunza evidence (QJE-published), newly independent from Twaweza, deploying AI-powered learning systems at scale."
- SOMA has a live pilot (Kibaha Term 3 2026) — not a theoretical idea.
- SOMA is NO LONGER a WhatsApp coaching programme. It is a learning measurement + ability grouping + data dashboard + AI analytics system. Update all materials accordingly.

**Domain / website:**
- learnimpact.org — PRIMARY domain (secured)
- learnimpact.or.tz — alias (secured)
- Website: in progress. Must include: Reg. 00NGO/R/8931, mission statement, board members, contact details.
- Website is a hard prerequisite for: Google for Nonprofits, Goodstack verification, any funder due diligence.

**Google.org next steps (in order):**
1. Complete learnimpact.org website (include reg number, mission, board, contact)
2. Submit to Goodstack with MoCS certificate + NGO Constitution (10-14 day turnaround)
3. Activate Google for Nonprofits → launch $10K/month Ad Grant
4. Build Google.org Africa team relationship (before any Impact Challenge call)
5. Apply to Impact Challenge when Africa window opens (watch Q4 2026 / 2027)
