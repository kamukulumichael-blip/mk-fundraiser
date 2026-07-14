#!/usr/bin/env python3
"""
Daily email dispatch — runs every day at 06:00 and 13:00 EAT via GitHub Actions.
Reads email_config.json, checks conditions, sends pipeline brief if due.
Imports sending logic from research.py to keep a single source of truth.
"""
import json, datetime, sys, os
from pathlib import Path

DATA_DIR = Path(__file__).parent / "data"
TODAY = datetime.datetime.utcnow().strftime("%Y-%m-%d")


def load_json(filename):
    p = DATA_DIR / filename
    if not p.exists():
        return {}
    with open(p) as f:
        return json.load(f)


def write_debug(info: dict):
    """Write debug state to data/email_debug.json so it's readable from the remote repo."""
    p = DATA_DIR / "email_debug.json"
    info["run_at_utc"] = datetime.datetime.utcnow().isoformat() + "Z"
    with open(p, "w") as f:
        json.dump(info, f, indent=2)


def main():
    from research import (
        load_email_config, save_email_config,
        should_send_today, build_email_html, send_via_gmail
    )

    gmail_user = os.environ.get("GMAIL_USER", "")
    # Strip spaces — Google displays app passwords with spaces but they're not part of the key
    gmail_pass = os.environ.get("GMAIL_APP_PASSWORD", "").replace(" ", "")
    os.environ["GMAIL_APP_PASSWORD"] = gmail_pass  # update so send_via_gmail uses stripped version

    today_name = datetime.datetime.utcnow().strftime("%A")
    cfg = load_email_config()

    # Manual workflow_dispatch → force send regardless of day schedule
    is_manual = os.environ.get("GITHUB_EVENT_NAME", "") == "workflow_dispatch"

    debug = {
        "gmail_user_set": bool(gmail_user),
        "gmail_user_value": gmail_user,
        "gmail_pass_set": bool(gmail_pass),
        "gmail_pass_len": len(gmail_pass),
        "today_utc": TODAY,
        "today_weekday": today_name,
        "is_manual_dispatch": is_manual,
        "config": cfg,
        "should_send": None,
        "send_result": None,
        "error": None
    }

    if not cfg:
        debug["error"] = "No email config found"
        write_debug(debug)
        return

    send = should_send_today(cfg, force=is_manual)
    debug["should_send"] = send

    if not send:
        debug["error"] = "should_send_today returned False — day/frequency/enabled check failed"
        write_debug(debug)
        print("Email not due — check email_debug.json for details.")
        return

    alerts = load_json("alerts.json")
    brief  = load_json("pipeline_monday_brief.json")
    debug["alerts_found"] = bool(alerts)
    debug["brief_found"] = bool(brief)

    if not alerts:
        debug["error"] = "alerts.json missing or empty"
        write_debug(debug)
        sys.exit(1)

    html = build_email_html(alerts, brief)
    week = alerts.get("week_number", "")
    subject = f"Raisr Pipeline Brief — Week {week} · {TODAY}"
    debug["subject"] = subject
    debug["recipients"] = cfg.get("recipients", [])

    try:
        sent = send_via_gmail(cfg["recipients"], subject, html)
        debug["send_result"] = "sent" if sent else "failed"
    except Exception as e:
        debug["send_result"] = "exception"
        debug["error"] = str(e)
        write_debug(debug)
        sys.exit(1)

    write_debug(debug)

    if sent:
        cfg["last_sent"] = datetime.datetime.utcnow().isoformat() + "Z"
        cfg["send_now"] = False
        save_email_config(cfg)
        print(f"Done. Email sent. last_sent={cfg['last_sent']}")
    else:
        print("ERROR: send_via_gmail returned False — check email_debug.json")
        sys.exit(1)


if __name__ == "__main__":
    main()
