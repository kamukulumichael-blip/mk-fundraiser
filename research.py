#!/usr/bin/env python3
"""
LearnImpact Fundraising Intelligence Hub — Weekly Research Script
Runs every Monday 06:00 EAT (03:00 UTC) via GitHub Actions.
Generates alerts.json with hot list, insights, priority shifts, and cross-programme conflicts.
"""

import json, os, datetime, anthropic, base64, requests, sys
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
{json.dumps([{{k: f.get(k) for k in ['id','name','tier','status','alignment_score','probability_score','effort_score','current_priorities','detected_priority_shift','recent_news']}} for f in funder_list[:20]], indent=2)}

ACTIVE OPPORTUNITIES:
{json.dumps(active_opps, indent=2)}

RELATIONSHIP NOTES:
{json.dumps([{{k: d.get(k) for k in ['contact_name','contact_role','relationship_stage','relationship_health','next_action','next_action_due','intelligence_notes']}} for d in donor_list], indent=2)}

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
            max_tokens=2048,
            messages=[{"role": "user", "content": prompt}]
        )
        text = msg.content[0].text
        # Extract JSON from response
        start = text.find("{")
        end = text.rfind("}") + 1
        if start >= 0 and end > start:
            return json.loads(text[start:end])
    except Exception as e:
        print(f"Error researching {programme}: {e}")
    return {
        "insight_of_week": f"Research unavailable for {programme} — retry next week.",
        "hot_list": [], "new_rfps": [], "new_funders_detected": [],
        "priority_shifts": [], "out_of_industry": [],
        "positioning_advice": ""
    }


def detect_cross_programme_conflicts(funders):
    """Detect funders appearing in multiple entity pools."""
    li_funders = {f["id"]: f["name"] for f in funders if f.get("entity") == "learnimpact"}
    ti_funders = {f["id"]: f["name"] for f in funders if f.get("entity") == "timamu"}
    # Also check by name for name-based matches
    li_names = {f["name"].lower(): f for f in funders if f.get("entity") == "learnimpact"}
    conflicts = []
    for fid, name in ti_funders.items():
        if fid in li_funders or name.lower() in li_names:
            li_f = li_funders.get(fid) or li_names.get(name.lower(), {}).get("name", name)
            progs_li = [p for f in funders if f.get("name") == li_f or f["id"] == fid
                        and f.get("entity") == "learnimpact" for p in f.get("programmes", [])]
            progs_ti = ["timamu"]
            conflicts.append({
                "funder_id": fid,
                "funder": name,
                "programmes": list(set(progs_li + progs_ti)) or ["learnimpact", "timamu"],
                "note": f"Same funder appears in both LearnImpact and Timamu pools. "
                        f"Coordinate before approaching — never allow simultaneous asks to same contact.",
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

    # Add overdue CRM touchpoints
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

    # Sort: high urgency first
    actions.sort(key=lambda a: (0 if a["urgency"] == "high" else 1, a.get("due", "")))
    return actions[:10]


def main():
    print(f"LearnImpact Fundraising Intelligence — Week {WEEK_NUM} ({TODAY})")

    funders_data   = load_json("funders.json")
    opps_data      = load_json("opportunities.json")
    donors_data    = load_json("donors.json")

    funders      = funders_data.get("funders", [])
    opportunities = opps_data.get("opportunities", [])
    donors       = donors_data.get("donors", [])

    print("Researching SOMA…")
    soma_res = research_programme("soma", funders, opportunities, donors)

    print("Researching KiuFunza…")
    kf_res = research_programme("kiufunza", funders, opportunities, donors)

    print("Researching Timamu…")
    timamu_res = research_programme("timamu", funders, opportunities, donors)

    conflicts = detect_cross_programme_conflicts(funders)

    upcoming = sorted(
        [o for o in opportunities if o.get("deadline") and o["stage"] not in ["won","lost"]],
        key=lambda o: o["deadline"]
    )
    today_str = datetime.date.today().isoformat()
    upcoming_dl = [{
        "opportunity_id": o["id"],
        "funder": next((f["name"] for f in funders if f["id"] == o.get("funder_id")), o.get("funder_id","")),
        "programme": o.get("programme", ""),
        "deadline": o["deadline"],
        "days_remaining": (datetime.date.fromisoformat(o["deadline"]) - datetime.date.today()).days
    } for o in upcoming[:10]]

    # Current funding gap (static seed — will be updated manually or via future automation)
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
        "cross_programme_conflicts": conflicts,
        "this_week_actions": this_week_actions,
        "upcoming_deadlines": upcoming_dl,
        "monday_brief_summary": monday_summary,
        "funding_gap": funding_gap
    }

    save_json("alerts.json", alerts)
    print("Generated alerts.json")

    # Update funder research dates
    for f in funders:
        if not f.get("last_research_date") or f["last_research_date"] < TODAY:
            f["last_research_date"] = TODAY
    save_json("funders.json", funders_data)

    print(f"Done. Week {WEEK_NUM} research complete.")


if __name__ == "__main__":
    main()
