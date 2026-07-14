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

API_KEY    = os.environ.get("ANTHROPIC_API_KEY", "")
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
    """Fetch funder-related emails and calendar events from Michael's M365 Outlook via Graph API.
    Prefers delegated flow (MS_REFRESH_TOKEN — no admin consent needed).
    Falls back to client credentials flow if refresh token not set."""
    tenant_id     = os.environ.get("MS_TENANT_ID", "")
    client_id     = os.environ.get("MS_CLIENT_ID", "")
    client_secret = os.environ.get("MS_CLIENT_SECRET", "")
    refresh_token = os.environ.get("MS_REFRESH_TOKEN", "")

    if not tenant_id or not client_id:
        print("MS365 credentials not set — skipping Outlook sync.")
        return {"emails": [], "events": [], "synced_at": TODAY, "error": "credentials_missing"}

    # Delegated flow: use refresh token (preferred — no admin consent needed)
    if refresh_token:
        token_resp = requests.post(
            f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token",
            data={
                "grant_type":    "refresh_token",
                "refresh_token": refresh_token,
                "client_id":     client_id,
                "scope":         "Mail.ReadBasic Calendars.Read offline_access",
            }
        )
    elif client_secret:
        # Application flow: requires admin consent (fallback)
        token_resp = requests.post(
            f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token",
            data={
                "grant_type":    "client_credentials",
                "client_id":     client_id,
                "client_secret": client_secret,
                "scope":         "https://graph.microsoft.com/.default",
            }
        )
    else:
        print("MS365: no refresh token or client secret — skipping.")
        return {"emails": [], "events": [], "synced_at": TODAY, "error": "no_auth_method"}

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
            "&$select=id,subject,start,end,attendees,body,onlineMeeting,bodyPreview"
            "&$top=20",
            headers=headers
        )
        if r.status_code == 200:
            for item in r.json().get("value", []):
                attendees = [a.get("emailAddress", {}).get("name", "") for a in item.get("attendees", [])[:5]]
                body_content = item.get("body", {}).get("content", "")
                # Strip HTML tags for plain-text preview
                import re as _re
                notes_preview = _re.sub(r'<[^>]+>', ' ', body_content).strip()[:600] if body_content else ""
                event_record = {
                    "subject": item.get("subject", ""),
                    "start": item.get("start", {}).get("dateTime", "")[:10],
                    "attendees": attendees,
                    "notes_preview": notes_preview
                }
                events.append(event_record)
            print(f"MS365: {len(events)} upcoming events.")
        else:
            print(f"MS365 calendar error {r.status_code}: {r.text[:200]}")
    except Exception as e:
        print(f"MS365 calendar exception: {e}")

    # Past meeting notes (last 30 days) — for briefing context
    meeting_notes = []
    try:
        past = (datetime.datetime.utcnow() - datetime.timedelta(days=30)).isoformat() + "Z"
        now_str = datetime.datetime.utcnow().isoformat() + "Z"
        r = requests.get(
            f"https://graph.microsoft.com/v1.0/users/{user}/calendarView"
            f"?startDateTime={past}&endDateTime={now_str}"
            "&$select=subject,start,end,attendees,body,bodyPreview"
            "&$top=15&$orderby=start/dateTime desc",
            headers=headers
        )
        if r.status_code == 200:
            import re as _re
            for item in r.json().get("value", []):
                body_content = item.get("body", {}).get("content", "")
                notes = _re.sub(r'<[^>]+>', ' ', body_content).strip()[:800] if body_content else item.get("bodyPreview", "")[:400]
                attendees = [a.get("emailAddress", {}).get("name", "") for a in item.get("attendees", [])[:6]]
                if notes.strip():
                    meeting_notes.append({
                        "date": item.get("start", {}).get("dateTime", "")[:10],
                        "title": item.get("subject", ""),
                        "notes": notes,
                        "attendees": attendees
                    })
            print(f"MS365: {len(meeting_notes)} past meetings with notes.")
        else:
            print(f"MS365 past meetings error {r.status_code}: {r.text[:100]}")
    except Exception as e:
        print(f"MS365 meeting notes exception: {e}")

    return {"emails": emails, "events": events, "meeting_notes": meeting_notes, "synced_at": TODAY}


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

    # Email brief dispatch (if configured)
    try:
        check_and_send_email(alerts, pipeline_brief)
    except Exception as e:
        print(f"Email dispatch error: {e}")


# ══════════════════════════════════════════════════════════════
# EMAIL BRIEF
# ══════════════════════════════════════════════════════════════
def load_email_config():
    cfg_path = DATA_DIR / "email_config.json"
    if not cfg_path.exists():
        return {}
    with open(cfg_path) as f:
        return json.load(f)


def save_email_config(cfg):
    cfg_path = DATA_DIR / "email_config.json"
    with open(cfg_path, "w") as f:
        json.dump(cfg, f, indent=2)


def should_send_today(cfg):
    """Return True if conditions are met to send the brief now."""
    if not cfg.get("enabled") or not cfg.get("recipients"):
        return False
    if cfg.get("send_now"):
        return True

    day_names = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]
    today_name = day_names[datetime.datetime.utcnow().weekday()]
    if cfg.get("send_day", "Monday") != today_name:
        return False

    # Frequency: biweekly = even ISO weeks; monthly = first occurrence of weekday in month
    freq = cfg.get("frequency", "weekly")
    if freq == "biweekly":
        week_num = int(datetime.datetime.utcnow().strftime("%V"))
        if week_num % 2 != 0:
            return False
    elif freq == "monthly":
        # First occurrence of send_day in the month
        today = datetime.datetime.utcnow()
        if today.day > 7:
            return False

    # Avoid double-send: check last_sent
    last_sent = cfg.get("last_sent")
    if last_sent and last_sent[:10] == TODAY:
        return False

    return True


def build_email_html(alerts, brief):
    """Build a clean branded HTML email from research outputs."""
    week = alerts.get("week_number", "")
    soma = alerts.get("soma", {})
    kf   = alerts.get("kiufunza", {})
    tim  = alerts.get("timamu", {})
    gap  = alerts.get("funding_gap", {})
    actions = (alerts.get("this_week_actions") or [])[:3]

    # Top 3 actions rows
    action_rows = ""
    for a in actions:
        urgency_color = {"high": "#BE6243", "medium": "#FFC650", "low": "#5EA6B8"}.get(a.get("urgency",""), "#5EA6B8")
        action_rows += f"""
        <tr>
          <td style="padding:8px 12px;border-bottom:1px solid #e8e8e8">
            <span style="display:inline-block;background:{urgency_color};color:#fff;font-size:10px;font-weight:700;
              padding:2px 7px;border-radius:10px;margin-right:6px;text-transform:uppercase">{a.get('urgency','')}</span>
            <strong style="font-size:12px;color:#354062">{a.get('funder','')}</strong>
            <span style="font-size:11px;color:#666;margin-left:4px">· {a.get('programme','').upper()}</span><br>
            <span style="font-size:12px;color:#333">{a.get('action','')}</span>
          </td>
        </tr>"""

    soma_pipeline = gap.get("soma_pipeline_usd", 0)
    soma_confirmed = gap.get("soma_confirmed_usd", 0)
    soma_needed = gap.get("soma_needed_usd", 0)

    brief_focus = ""
    if brief and brief.get("this_week_focus"):
        brief_focus = f"""
        <tr><td style="padding:16px 24px 0">
          <p style="margin:0;font-size:13px;font-style:italic;color:#354062;border-left:3px solid #FFC650;padding-left:12px">
            {brief['this_week_focus']}</p>
        </td></tr>"""

    return f"""<!DOCTYPE html>
<html><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Raisr Pipeline Brief — Week {week}</title></head>
<body style="margin:0;padding:0;background:#f4f4f4;font-family:'Helvetica Neue',Arial,sans-serif">
<table width="100%" cellpadding="0" cellspacing="0" style="background:#f4f4f4;padding:24px 0">
<tr><td align="center">
<table width="600" cellpadding="0" cellspacing="0" style="background:#fff;border-radius:8px;overflow:hidden;
  box-shadow:0 2px 8px rgba(0,0,0,.08);max-width:600px;width:100%">

  <!-- Header -->
  <tr><td style="background:#354062;padding:24px 28px">
    <p style="margin:0;font-size:11px;font-weight:700;color:#FFC650;text-transform:uppercase;letter-spacing:.08em">
      LearnImpact · Raisr</p>
    <h1 style="margin:4px 0 0;font-size:22px;font-weight:800;color:#fff">
      Pipeline Brief · Week {week}</h1>
    <p style="margin:6px 0 0;font-size:12px;color:rgba(255,255,255,.6)">{TODAY}</p>
  </td></tr>

  {brief_focus}

  <!-- Top actions -->
  <tr><td style="padding:20px 24px 8px">
    <p style="margin:0 0 10px;font-size:11px;font-weight:700;color:#888;text-transform:uppercase;letter-spacing:.08em">
      This Week's Actions</p>
    <table width="100%" cellpadding="0" cellspacing="0" style="border:1px solid #e8e8e8;border-radius:6px;overflow:hidden">
      {action_rows if action_rows else '<tr><td style="padding:12px;color:#999;font-size:12px">No actions this week.</td></tr>'}
    </table>
  </td></tr>

  <!-- Programme insights -->
  <tr><td style="padding:16px 24px 8px">
    <p style="margin:0 0 12px;font-size:11px;font-weight:700;color:#888;text-transform:uppercase;letter-spacing:.08em">
      Programme Insights</p>
    {"".join([f'''<div style="margin-bottom:10px;padding:12px 14px;background:#f9f9f9;border-radius:6px;border-left:3px solid {'#354062' if prog=='SOMA' else '#5EA6B8' if prog=='KiuFunza' else '#BE6243'}">
      <span style="font-size:10px;font-weight:700;color:#888;text-transform:uppercase">{prog}</span>
      <p style="margin:4px 0 0;font-size:12px;color:#333">{res.get('insight_of_week','—')}</p>
    </div>''' for prog, res in [("SOMA", soma), ("KiuFunza", kf), ("Timamu", tim)] if res.get('insight_of_week')])}
  </td></tr>

  <!-- Funding gap -->
  <tr><td style="padding:16px 24px">
    <p style="margin:0 0 10px;font-size:11px;font-weight:700;color:#888;text-transform:uppercase;letter-spacing:.08em">
      SOMA Funding Gap</p>
    <table width="100%" cellpadding="0" cellspacing="0">
      <tr>
        <td style="font-size:12px;color:#666">Confirmed</td>
        <td style="font-size:12px;color:#666">Pipeline</td>
        <td style="font-size:12px;color:#666">Needed</td>
      </tr>
      <tr>
        <td style="font-size:16px;font-weight:700;color:#1A7060">${soma_confirmed:,.0f}</td>
        <td style="font-size:16px;font-weight:700;color:#354062">${soma_pipeline:,.0f}</td>
        <td style="font-size:16px;font-weight:700;color:#BE6243">${soma_needed:,.0f}</td>
      </tr>
    </table>
  </td></tr>

  <!-- Footer -->
  <tr><td style="background:#f0f2f7;padding:16px 24px;border-top:1px solid #e0e4ef">
    <p style="margin:0;font-size:11px;color:#888">
      Raisr Pipeline Intelligence · LearnImpact, Dar es Salaam<br>
      Generated automatically · <a href="https://kamukulumichael-blip.github.io/mk-fundraiser/"
        style="color:#354062">Open dashboard</a>
    </p>
  </td></tr>

</table>
</td></tr></table>
</body></html>"""


def send_via_gmail(recipients, subject, html_body):
    """Send HTML email via Gmail SMTP using app password."""
    import smtplib
    from email.mime.multipart import MIMEMultipart
    from email.mime.text import MIMEText

    gmail_user = os.environ.get("GMAIL_USER", "")
    gmail_pass = os.environ.get("GMAIL_APP_PASSWORD", "")
    if not gmail_user or not gmail_pass:
        print("Email: GMAIL_USER / GMAIL_APP_PASSWORD not set — skipping.")
        return False

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = f"Raisr · LearnImpact <{gmail_user}>"
    msg["To"] = ", ".join(recipients)
    msg.attach(MIMEText(html_body, "html", "utf-8"))

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
            smtp.login(gmail_user, gmail_pass)
            smtp.sendmail(gmail_user, recipients, msg.as_string())
        print(f"Email sent to {len(recipients)} recipient(s).")
        return True
    except Exception as e:
        print(f"Email send failed: {e}")
        return False


def check_and_send_email(alerts, brief):
    """Send the pipeline brief by email if configured and conditions are met."""
    cfg = load_email_config()
    if not should_send_today(cfg):
        return

    html = build_email_html(alerts, brief)
    week = alerts.get("week_number", "")
    subject = f"Raisr Pipeline Brief — Week {week} · {TODAY}"
    sent = send_via_gmail(cfg["recipients"], subject, html)

    if sent:
        cfg["last_sent"] = datetime.datetime.utcnow().isoformat() + "Z"
        cfg["send_now"] = False
        save_email_config(cfg)
        print(f"Email config updated with last_sent={cfg['last_sent']}")


if __name__ == "__main__":
    main()
