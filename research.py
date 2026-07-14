#!/usr/bin/env python3
"""
LearnImpact Fundraising Intelligence Hub — Weekly Research Script
Runs every Monday 06:00 EAT (03:00 UTC) via GitHub Actions.
Generates alerts.json with hot list, insights, priority shifts, cross-programme conflicts,
and source intelligence feed from registered websites/LinkedIn creators.
"""

import json, os, datetime, anthropic, base64, requests, sys
try:
    from json_repair import repair_json as _repair
except ImportError:
    _repair = None

def parse_json(text):
    start = text.find("{")
    end = text.rfind("}") + 1
    if start < 0 or end <= start:
        return None
    raw = text[start:end]
    try:
        return json.loads(raw)
    except Exception:
        if _repair:
            try:
                return json.loads(_repair(raw))
            except Exception:
                pass
    return None
from pathlib import Path

API_KEY    = os.environ["ANTHROPIC_API_KEY"]
GH_TOKEN   = os.environ.get("GITHUB_TOKEN", "")
GH_REPO    = os.environ.get("GITHUB_REPOSITORY", "kamukulumichael-blip/mk-fundraiser")
DATA_DIR   = Path(__file__).parent / "data"
TODAY      = datetime.date.today().isoformat()
WEEK_NUM   = datetime.date.today().isocalendar()[1]

client = anthropic.Anthropic(api_key=API_KEY)

LEARNIMPACT_CONTEXT = """
LearnImpact is an evidence-based learning systems transformation organisation in Dar es Salaam, Tanzania.
Newly independent from Twaweza, May 2026. Executive Director: Michael Kamukulu.
5-Year Architecture: Prove → Partner → Embed → Replicate (Tanzania → Zanzibar → Burundi → East Africa).

SOMA Programme: AI-enabled foundational learning. WhatsApp coaching chatbot (Mwalimu) for teachers.
USD 3.12/student/year. Kibaha pilot Term 3 2026 (10 schools). Mtwara RCT 2027 (70 schools).
USD 12/LAYS modelled. Government co-financing: Kibaha District Council.
Active asks: Founders Pledge $5M (in review), VTF SOMA (not started), Dovetail Track 2 (not started).
2027 funding gap: $637K (USD 229K confirmed vs USD 866K needed).

KiuFunza Programme: Teacher performance pay, Grades 1-7. 265 schools.
QJE-published: +9.4pp treatment effect. USD 7/child/year.
Active funders: Hempel (anchor, Hearing Committee), VTF (TZS 462M near-confirmed), Dovetail ($100K Track 1 won).
CRITICAL: Never lead with Twaweza history. GoT sensitivity — brand damaging.
""".strip()

TIMAMU_CONTEXT = """
Timamu Foundation: SEPARATE LEGAL ENTITY from LearnImpact. Founder: Michael Kamukulu.
Focus: Persons with disabilities + creator economy + assistive technology.
9-10M Tanzanians with disabilities. Tanzania Vision 2050: TZS 2B creator economy fund July 2026.
Phase 1: digital creation, assistive technology. Phase 2: gig economy, AI tools for PWDs.
Brand colors: Deep Plum, Vivid Coral, Forest Teal. NOT LearnImpact colors.
Active opportunities: Microsoft AI for Accessibility ($150K, rolling),
Adobe Foundation ($50K, rolling), Tanzania creator economy fund, Ford Foundation ($15M disability commitment April 2025).
CRITICAL: Never reference LearnImpact as implementing entity for Timamu.
""".strip()

PIPELINE_BRIEF_SYSTEM = """You are Pipeline — LearnImpact's fundraising strategy agent. Monday Mode 3: automated weekly scan.
Produce a Monday briefing for Michael Kamukulu (Executive Director). Be specific, named, opinionated.
The 2027 SOMA gap is the urgent constraint: USD 229K confirmed / USD 866K needed / Gap: USD 637K.
Locked cost evidence: SOMA = USD 3.12/student/year; KiuFunza = +9.4pp (Quarterly Journal of Economics).
LearnImpact is NOT a startup — established NGO Reg. 00NGO/R/8931, 10+ years evidence, newly independent from Twaweza May 2026.
Never re-derive cost figures. Michael owns all donor relationships. Name names. Flag risks early.

Return ONLY valid JSON:
{
  "this_week_focus": "One sentence — the single most important thing Michael should focus on this week. Name names and numbers.",
  "top_3_actions": [
    {
      "action": "Exact, specific action — not vague",
      "funder": "Funder or contact name",
      "programme": "soma|kiufunza|timamu",
      "urgency": "high|medium",
      "reasoning": "Why this specific week — what changes if this is delayed"
    }
  ],
  "pipeline_health": {
    "soma": "One sentence with specific numbers and named funders",
    "kiufunza": "One sentence — include VTF signing and Hempel status",
    "timamu": "One sentence",
    "concentration_risk": "Specific named risk or null",
    "gap_progress": "Honest trajectory — specific and named"
  },
  "positioning_move": "What Michael should publish, speak, or post in the next 7 days to stay visible with the top prospect",
  "flags": [
    {
      "flag": "Specific named risk or opportunity",
      "urgency": "high|medium",
      "response": "Recommended action"
    }
  ],
  "weekly_narrative": "3-4 sentences. Pipeline's strategic read. Named funders, amounts, timelines. What matters most and what is at risk if nothing moves."
}"""


def load_json(filename):
    try:
        with open(DATA_DIR / filename) as f:
            return json.load(f)
    except Exception as e:
        print(f"Warning: could not load {filename}: {e}")
        return {}


def save_json(filename, data):
    with open(DATA_DIR / filename, "w") as f:
        json.dump(data, f, indent=2)
    print(f"Saved {filename}")


def research_programme(programme, funders, opportunities, donors):
    """Call Claude to research and generate weekly intelligence for one programme."""
    funder_list = [f for f in funders if programme in f.get("programmes", [])]
    active_opps = [o for o in opportunities if o.get("programme") == programme and
                   o.get("stage") not in ["won", "lost"]]
    donor_list = [d for d in donors if programme in d.get("programmes", [])]

    ctx = TIMAMU_CONTEXT if programme == "timamu" else LEARNIMPACT_CONTEXT

    prompt = f"""You are a world-class fundraising intelligence analyst for {programme.upper()}.

Today: {TODAY}. Week: {WEEK_NUM}.

PROGRAMME CONTEXT:
{ctx}

CURRENT FUNDER DATABASE ({len(funder_list)} funders for {programme}):
{json.dumps([{k: f.get(k) for k in ['id','name','tier','status','alignment_score','probability_score','effort_score','current_priorities','detected_priority_shift','recent_news']} for f in funder_list[:20]], indent=2)}

ACTIVE OPPORTUNITIES:
{json.dumps(active_opps, indent=2)}

RELATIONSHIP NOTES:
{json.dumps([{k: d.get(k) for k in ['contact_name','contact_role','relationship_stage','relationship_health','next_action','next_action_due','intelligence_notes']} for d in donor_list], indent=2)}

Generate a weekly intelligence brief for {programme.upper()}. Return ONLY valid JSON with this exact structure:
{{
  "insight_of_week": "One specific, named, actionable insight — NOT a generic summary. Name a funder, a number, a deadline.",
  "hot_list": [
    {{"funder_id": "string", "why_now": "specific reason this week", "recommended_action": "exact next step", "deadline": "YYYY-MM-DD or null", "composite_score": 0}}
  ],
  "new_rfps": [
    {{"title": "string", "funder": "string", "funder_id": "string or null", "deadline": "YYYY-MM-DD", "amount_usd": 0, "why_it_fits": "string"}}
  ],
  "new_funders_detected": [
    {{"name": "string", "why_it_fits": "string", "suggested_tier": 2, "action": "string"}}
  ],
  "priority_shifts": [
    {{"funder_id": "string", "funder": "string", "what_changed": "string", "action": "string", "urgency": "high|medium"}}
  ],
  "out_of_industry": [
    {{"funder": "string", "sector": "string", "why_it_fits": "string", "action": "string"}}
  ],
  "positioning_advice": "What Michael should publish or speak about in the next 30 days to stay warm with the top prospects"
}}

Hot list scores: composite = (alignment/100) × (probability/100) × deadline_urgency × (6 - effort)
where deadline_urgency = 5 if <30 days, 3 if 30-90 days, 2 if 90-180 days, 1 if no deadline.
Include up to 7 funders in hot_list, ranked by composite score descending.
Only include funders from the database. Use their exact funder_id values.
Be specific and actionable. No generic advice."""

    try:
        msg = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=4096,
            messages=[{"role": "user", "content": prompt}]
        )
        parsed = parse_json(msg.content[0].text)
        if parsed:
            return parsed
    except Exception as e:
        err_msg = str(e)
        print(f"Error researching {programme}: {err_msg}")
        return {
            "insight_of_week": f"API error — {err_msg[:200]}",
            "hot_list": [], "new_rfps": [], "new_funders_detected": [],
            "priority_shifts": [], "out_of_industry": [],
            "positioning_advice": ""
        }
    return {
        "insight_of_week": f"Research unavailable for {programme} — retry next week.",
        "hot_list": [], "new_rfps": [], "new_funders_detected": [],
        "priority_shifts": [], "out_of_industry": [],
        "positioning_advice": ""
    }


def web_research_sources(sources):
    """Use Claude with web_search to gather intelligence from registered sources.
    Returns a list of findings relevant to LearnImpact / Timamu programmes."""
    active = [s for s in sources if s.get("active", True)]
    if not active:
        print("No active sources — skipping web research.")
        return []

    source_lines = "\n".join([
        f"- {s['name']}: {s.get('url', 'no URL')} ({', '.join(s.get('programmes', []))})"
        for s in active[:12]
    ])

    prompt = f"""You are a fundraising intelligence analyst for LearnImpact (SOMA, KiuFunza) and Timamu Foundation in Tanzania. Today: {TODAY}.

Search the following intelligence sources for the past 7 days of relevant content:

REGISTERED SOURCES TO CHECK:
{source_lines}

Also search for:
- New RFPs or grant calls matching: foundational learning, teacher coaching, AI in education, East Africa education, disability inclusion Tanzania
- Any announcements from these funders: Gates Foundation, Founders Pledge, Hempel Foundation, Dovetail/Prevail Fund, Vodacom Foundation, Ford Foundation, Microsoft AI for Accessibility, Adobe Foundation, GPE, FCDO
- LinkedIn posts (past 7 days) about: education funding Africa, evidence-based development grants, disability inclusion funding, AI education technology grants
- Tanzania education news that signals government funding appetite or World Bank / GPE activity

For each finding, assess relevance to:
- SOMA (AI teacher coaching, foundational learning, Tanzania, $3/student)
- KiuFunza (teacher performance pay, QJE evidence, East Africa)
- Timamu (PWD inclusion, assistive technology, creator economy)

Return ONLY valid JSON:
{{
  "findings": [
    {{
      "source": "source name",
      "title": "specific headline or finding",
      "relevance": "soma|kiufunza|timamu|learnimpact",
      "why_relevant": "specific reason — name the funder/RFP/amount if applicable",
      "url": "url or null",
      "action": "exact next step for Michael",
      "urgency": "high|medium|low"
    }}
  ]
}}

Only include genuinely relevant findings. Maximum 10 findings. Be specific — name funders, amounts, deadlines."""

    try:
        print("Running web research across registered sources…")
        msg = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=2000,
            tools=[{"type": "web_search_20250305", "name": "web_search"}],
            messages=[{"role": "user", "content": prompt}]
        )
        # Collect text from all content blocks (Claude may have done multiple searches)
        full_text = ""
        for block in msg.content:
            if hasattr(block, "text"):
                full_text += block.text
        start = full_text.find("{")
        end = full_text.rfind("}") + 1
        if start >= 0 and end > start:
            result = json.loads(full_text[start:end])
            findings = result.get("findings", [])
            print(f"Web research: {len(findings)} findings.")
            return findings
    except Exception as e:
        print(f"Web research error (continuing without): {e}")
    return []


def fetch_ms365_intelligence():
    """Fetch funder-related emails and calendar events from Michael's M365 Outlook via Graph API."""
    tenant_id = os.environ.get("MS_TENANT_ID", "")
    client_id = os.environ.get("MS_CLIENT_ID", "")
    client_secret = os.environ.get("MS_CLIENT_SECRET", "")

    if not all([tenant_id, client_id, client_secret]):
        print("MS365 credentials not set — skipping Outlook sync.")
        return {"emails": [], "events": [], "synced_at": TODAY, "error": "credentials_missing"}

    token_resp = requests.post(
        f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token",
        data={
            "grant_type": "client_credentials",
            "client_id": client_id,
            "client_secret": client_secret,
            "scope": "https://graph.microsoft.com/.default"
        }
    )
    if token_resp.status_code != 200:
        err = token_resp.text[:200]
        print(f"MS365 token error {token_resp.status_code}: {err}")
        return {"emails": [], "events": [], "synced_at": TODAY, "error": f"token_{token_resp.status_code}"}

    token = token_resp.json().get("access_token", "")
    headers = {"Authorization": f"Bearer {token}"}
    user = "mkamukulu@learnimpact.org"

    emails = []
    try:
        r = requests.get(
            f"https://graph.microsoft.com/v1.0/users/{user}/messages"
            "?$search=\"VTF OR Hempel OR Founders OR Lorcan OR Sandra OR Dovetail OR Vodacom OR Rosa\""
            "&$top=20"
            "&$select=subject,from,receivedDateTime,bodyPreview",
            headers=headers
        )
        if r.status_code == 200:
            for item in r.json().get("value", []):
                emails.append({
                    "subject": item.get("subject", ""),
                    "from": item.get("from", {}).get("emailAddress", {}).get("name", ""),
                    "from_email": item.get("from", {}).get("emailAddress", {}).get("address", ""),
                    "received": item.get("receivedDateTime", "")[:10],
                    "preview": item.get("bodyPreview", "")[:400]
                })
            print(f"MS365: {len(emails)} funder emails.")
        else:
            print(f"MS365 email error {r.status_code}: {r.text[:200]}")
    except Exception as e:
        print(f"MS365 email exception: {e}")

    events = []
    try:
        now = datetime.datetime.utcnow().isoformat() + "Z"
        future = (datetime.datetime.utcnow() + datetime.timedelta(days=45)).isoformat() + "Z"
        r = requests.get(
            f"https://graph.microsoft.com/v1.0/users/{user}/calendarView"
            f"?startDateTime={now}&endDateTime={future}"
            "&$select=subject,start,end,attendees"
            "&$top=20",
            headers=headers
        )
        if r.status_code == 200:
            for item in r.json().get("value", []):
                attendees = [a.get("emailAddress", {}).get("name", "") for a in item.get("attendees", [])[:5]]
                events.append({
                    "subject": item.get("subject", ""),
                    "start": item.get("start", {}).get("dateTime", "")[:10],
                    "attendees": attendees
                })
            print(f"MS365: {len(events)} upcoming events.")
        else:
            print(f"MS365 calendar error {r.status_code}: {r.text[:200]}")
    except Exception as e:
        print(f"MS365 calendar exception: {e}")

    return {"emails": emails, "events": events, "synced_at": TODAY}


def detect_cross_programme_conflicts(funders):
    """Detect funders appearing in multiple entity pools."""
    li_funders = {f["id"]: f["name"] for f in funders if f.get("entity") == "learnimpact"}
    ti_funders = {f["id"]: f["name"] for f in funders if f.get("entity") == "timamu"}
    li_names = {f["name"].lower(): f for f in funders if f.get("entity") == "learnimpact"}
    conflicts = []
    for fid, name in ti_funders.items():
        if fid in li_funders or name.lower() in li_names:
            li_f = li_funders.get(fid) or li_names.get(name.lower(), {}).get("name", name)
            progs_li = [p for f in funders if (f.get("name") == li_f or f["id"] == fid)
                        and f.get("entity") == "learnimpact" for p in f.get("programmes", [])]
            conflicts.append({
                "funder_id": fid,
                "funder": name,
                "programmes": list(set(progs_li + ["timamu"])) or ["learnimpact", "timamu"],
                "note": "Same funder appears in both LearnImpact and Timamu pools. "
                        "Coordinate before approaching — never allow simultaneous asks to same contact.",
                "recommended_sequence": "Decide priority entity first. LearnImpact asks first if active programme ongoing."
            })
    return conflicts


def generate_monday_brief(soma_res, kf_res, timamu_res, opportunities, funding_gap):
    """Generate the Monday executive summary."""
    actions_summary = []
    for prog, res in [("SOMA", soma_res), ("KiuFunza", kf_res), ("Timamu", timamu_res)]:
        hot = res.get("hot_list", [])
        if hot:
            top = hot[0]
            actions_summary.append(f"{prog}: {top.get('recommended_action','')}")

    upcoming = sorted(
        [o for o in opportunities if o.get("deadline") and o["stage"] not in ["won","lost"]],
        key=lambda o: o["deadline"]
    )[:5]

    summary_parts = [
        f"Week {WEEK_NUM} ({TODAY}).",
        f"SOMA insight: {soma_res.get('insight_of_week','')}",
        f"KiuFunza insight: {kf_res.get('insight_of_week','')}",
        f"Timamu insight: {timamu_res.get('insight_of_week','')}",
        f"Top actions: {' | '.join(actions_summary[:3])}",
    ]
    if upcoming:
        next_dl = upcoming[0]
        summary_parts.append(f"Next deadline: {next_dl.get('title','Opportunity')} — {next_dl['deadline']}.")

    return "\n\n".join(summary_parts)


def build_this_week_actions(soma_res, kf_res, timamu_res, donors):
    """Compile prioritised action list from all three programmes + overdue CRM."""
    actions = []
    today = datetime.date.today()

    for prog, res in [("soma", soma_res), ("kiufunza", kf_res), ("timamu", timamu_res)]:
        for h in (res.get("hot_list") or [])[:3]:
            fid = h.get("funder_id", "")
            actions.append({
                "action": h.get("recommended_action", ""),
                "funder": fid,
                "programme": prog,
                "due": h.get("deadline") or (today + datetime.timedelta(days=14)).isoformat(),
                "urgency": "high" if (h.get("composite_score") or 0) >= 80 else "medium"
            })

    for d in donors:
        tp_date = (d.get("last_touchpoint") or {}).get("date")
        if tp_date:
            days_since = (today - datetime.date.fromisoformat(tp_date)).days
            if days_since > 60 and d.get("relationship_stage") in ["warm", "cultivating", "submitted"]:
                actions.append({
                    "action": f"Touchpoint overdue ({days_since}d) — reconnect with {d['contact_name']}",
                    "funder": d.get("contact_name", ""),
                    "programme": (d.get("programmes") or ["soma"])[0],
                    "due": today.isoformat(),
                    "urgency": "high"
                })

    actions.sort(key=lambda a: (0 if a["urgency"] == "high" else 1, a.get("due", "")))
    return actions[:10]


def run_pipeline_brief(soma_res, kf_res, timamu_res, opportunities, donors, monday_summary, ms365_intel=None):
    """Generate automated Pipeline Monday brief using Pipeline agent reasoning."""
    active_opps = [o for o in opportunities if o.get("stage") not in ["won", "lost"]]
    hot_donors = [d for d in donors if d.get("relationship_health") in ["hot", "warm"]]

    ms365_block = ""
    if ms365_intel and (ms365_intel.get("emails") or ms365_intel.get("events")):
        recent_emails = ms365_intel.get("emails", [])[:8]
        upcoming_events = ms365_intel.get("events", [])[:8]
        ms365_block = f"""

OUTLOOK INTELLIGENCE (synced {ms365_intel.get('synced_at', TODAY)}):
Recent funder emails ({len(recent_emails)}):
{json.dumps(recent_emails, indent=2)}

Upcoming calendar events ({len(upcoming_events)}):
{json.dumps(upcoming_events, indent=2)}"""

    context = f"""WEEKLY INTELLIGENCE — {TODAY} (Week {WEEK_NUM})

MONDAY BRIEF:
{monday_summary}{ms365_block}

ACTIVE PIPELINE:
{json.dumps([{k: o.get(k) for k in ['title','programme','stage','ask_amount_usd','deadline','outcome','won_lost_notes']} for o in active_opps[:8]], indent=2)}

CRM — HOT/WARM CONTACTS:
{json.dumps([{k: d.get(k) for k in ['contact_name','contact_role','relationship_health','next_action','next_action_due']} for d in hot_donors], indent=2)}

SOMA INTELLIGENCE:
Insight: {soma_res.get('insight_of_week','')}
Top hot-list: {json.dumps((soma_res.get('hot_list') or [{}])[0], indent=2)}
New RFPs detected: {len(soma_res.get('new_rfps',[]))}
Priority shifts: {len(soma_res.get('priority_shifts',[]))}

KIUFUNZA INTELLIGENCE:
Insight: {kf_res.get('insight_of_week','')}

TIMAMU INTELLIGENCE:
Insight: {timamu_res.get('insight_of_week','')}
"""
    try:
        print("Generating Pipeline Monday brief…")
        msg = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=2048,
            system=PIPELINE_BRIEF_SYSTEM,
            messages=[{"role": "user", "content": context}]
        )
        result = parse_json(msg.content[0].text)
        if result:
            result["generated_at"] = TODAY
            result["week_number"] = WEEK_NUM
            return result
    except Exception as e:
        err_msg = str(e)
        print(f"Pipeline brief error: {err_msg}")
        return {
            "generated_at": TODAY,
            "week_number": WEEK_NUM,
            "this_week_focus": f"Pipeline brief error — {err_msg[:200]}",
            "top_3_actions": [],
            "pipeline_health": {"soma": "", "kiufunza": "", "timamu": "", "concentration_risk": None, "gap_progress": ""},
            "positioning_move": "",
            "flags": [],
            "weekly_narrative": ""
        }
    return {
        "generated_at": TODAY,
        "week_number": WEEK_NUM,
        "this_week_focus": "Pipeline brief unavailable — check logs and retry.",
        "top_3_actions": [],
        "pipeline_health": {"soma": "", "kiufunza": "", "timamu": "", "concentration_risk": None, "gap_progress": ""},
        "positioning_move": "",
        "flags": [],
        "weekly_narrative": ""
    }


def main():
    print(f"LearnImpact Fundraising Intelligence — Week {WEEK_NUM} ({TODAY})")

    funders_data   = load_json("funders.json")
    opps_data      = load_json("opportunities.json")
    donors_data    = load_json("donors.json")
    sources_data   = load_json("sources.json")

    funders       = funders_data.get("funders", [])
    opportunities = opps_data.get("opportunities", [])
    donors        = donors_data.get("donors", [])
    sources       = sources_data.get("sources", [])

    print("Syncing MS365 Outlook intelligence…")
    ms365_intel = fetch_ms365_intelligence()

    print("Researching SOMA…")
    soma_res = research_programme("soma", funders, opportunities, donors)

    print("Researching KiuFunza…")
    kf_res = research_programme("kiufunza", funders, opportunities, donors)

    print("Researching Timamu…")
    timamu_res = research_programme("timamu", funders, opportunities, donors)

    # Web research across registered intelligence sources
    source_feed = web_research_sources(sources)

    conflicts = detect_cross_programme_conflicts(funders)

    upcoming = sorted(
        [o for o in opportunities if o.get("deadline") and o["stage"] not in ["won","lost"]],
        key=lambda o: o["deadline"]
    )
    upcoming_dl = [{
        "opportunity_id": o["id"],
        "funder": next((f["name"] for f in funders if f["id"] == o.get("funder_id")), o.get("funder_id","")),
        "programme": o.get("programme", ""),
        "deadline": o["deadline"],
        "days_remaining": (datetime.date.fromisoformat(o["deadline"]) - datetime.date.today()).days
    } for o in upcoming[:10]]

    funding_gap = {
        "soma_confirmed_usd": 229000,
        "soma_needed_usd": 866000,
        "soma_pipeline_usd": 5478000,
        "kiufunza_confirmed_usd": 765000,
        "kiufunza_needed_usd": 765000,
        "kiufunza_pipeline_usd": 0,
        "timamu_confirmed_usd": 0,
        "timamu_pipeline_usd": 400000
    }

    this_week_actions = build_this_week_actions(soma_res, kf_res, timamu_res, donors)
    monday_summary = generate_monday_brief(soma_res, kf_res, timamu_res, opportunities, funding_gap)

    alerts = {
        "generated_at": TODAY,
        "week_number": WEEK_NUM,
        "soma": soma_res,
        "kiufunza": kf_res,
        "timamu": timamu_res,
        "source_feed": source_feed,
        "ms365_sync": ms365_intel,
        "cross_programme_conflicts": conflicts,
        "this_week_actions": this_week_actions,
        "upcoming_deadlines": upcoming_dl,
        "monday_brief_summary": monday_summary,
        "funding_gap": funding_gap
    }

    save_json("alerts.json", alerts)
    print("Generated alerts.json")

    # Pipeline Monday brief — automated agent analysis
    pipeline_brief = run_pipeline_brief(soma_res, kf_res, timamu_res, opportunities, donors, monday_summary, ms365_intel)
    save_json("pipeline_monday_brief.json", pipeline_brief)
    print("Generated pipeline_monday_brief.json")

    for f in funders:
        if not f.get("last_research_date") or f["last_research_date"] < TODAY:
            f["last_research_date"] = TODAY
    save_json("funders.json", funders_data)

    print(f"Done. Week {WEEK_NUM} research complete.")


if __name__ == "__main__":
    main()
