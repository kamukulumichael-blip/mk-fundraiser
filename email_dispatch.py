#!/usr/bin/env python3
"""
Daily email dispatch — runs every day at 06:00 and 13:00 EAT via GitHub Actions.
Reads email_config.json, checks conditions, sends pipeline brief if due.
Imports sending logic from research.py to keep a single source of truth.
"""
import json, datetime
from pathlib import Path

DATA_DIR = Path(__file__).parent / "data"
TODAY = datetime.datetime.utcnow().strftime("%Y-%m-%d")


def load_json(filename):
    p = DATA_DIR / filename
    if not p.exists():
        return {}
    with open(p) as f:
        return json.load(f)


def main():
    from research import (
        load_email_config, save_email_config,
        should_send_today, build_email_html, send_via_gmail
    )

    cfg = load_email_config()
    if not cfg:
        print("No email config found — nothing to do.")
        return

    if not should_send_today(cfg):
        print(f"Email not due today ({TODAY}, {datetime.datetime.utcnow().strftime('%A')}) — skipping.")
        return

    alerts = load_json("alerts.json")
    brief  = load_json("pipeline_monday_brief.json")

    if not alerts:
        print("No alerts.json found — cannot build email.")
        return

    html = build_email_html(alerts, brief)
    week = alerts.get("week_number", "")
    subject = f"Raisr Pipeline Brief — Week {week} · {TODAY}"
    sent = send_via_gmail(cfg["recipients"], subject, html)

    if sent:
        cfg["last_sent"] = datetime.datetime.utcnow().isoformat() + "Z"
        cfg["send_now"] = False
        save_email_config(cfg)
        print(f"Email dispatched. last_sent updated.")


if __name__ == "__main__":
    main()
