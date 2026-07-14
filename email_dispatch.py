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


def main():
    from research import (
        load_email_config, save_email_config,
        should_send_today, build_email_html, send_via_gmail
    )

    # Diagnostics — always print so logs show state
    gmail_user = os.environ.get("GMAIL_USER", "")
    gmail_pass = os.environ.get("GMAIL_APP_PASSWORD", "")
    print(f"GMAIL_USER set: {'yes (' + gmail_user + ')' if gmail_user else 'NO — secret missing'}")
    print(f"GMAIL_APP_PASSWORD set: {'yes (' + str(len(gmail_pass)) + ' chars)' if gmail_pass else 'NO — secret missing'}")

    cfg = load_email_config()
    print(f"Email config: enabled={cfg.get('enabled')}, recipients={cfg.get('recipients')}, "
          f"send_day={cfg.get('send_day')}, frequency={cfg.get('frequency')}, last_sent={cfg.get('last_sent')}")

    if not cfg:
        print("No email config found — nothing to do.")
        return

    today_name = datetime.datetime.utcnow().strftime("%A")
    print(f"Today: {TODAY} ({today_name})")

    if not should_send_today(cfg):
        print(f"Email not due today — skipping.")
        return

    print("Conditions met — building email...")
    alerts = load_json("alerts.json")
    brief  = load_json("pipeline_monday_brief.json")

    if not alerts:
        print("ERROR: No alerts.json found — cannot build email.")
        sys.exit(1)

    html = build_email_html(alerts, brief)
    week = alerts.get("week_number", "")
    subject = f"Raisr Pipeline Brief — Week {week} · {TODAY}"
    print(f"Sending to: {cfg['recipients']}  Subject: {subject}")

    sent = send_via_gmail(cfg["recipients"], subject, html)

    if sent:
        cfg["last_sent"] = datetime.datetime.utcnow().isoformat() + "Z"
        cfg["send_now"] = False
        save_email_config(cfg)
        print(f"Done. last_sent={cfg['last_sent']}")
    else:
        print("ERROR: send_via_gmail returned False — check Gmail credentials above.")
        sys.exit(1)


if __name__ == "__main__":
    main()
