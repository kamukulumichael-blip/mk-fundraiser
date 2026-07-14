#!/usr/bin/env python3
"""
Daily email dispatch — runs every day at 06:00 and 13:00 EAT via GitHub Actions.
Reads email_config.json, checks conditions, sends pipeline brief if due.
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

    # Strip spaces — Google shows app passwords with spaces, they're cosmetic
    gmail_pass = os.environ.get("GMAIL_APP_PASSWORD", "").replace(" ", "")
    os.environ["GMAIL_APP_PASSWORD"] = gmail_pass

    cfg = load_email_config()
    if not cfg:
        print("No email config found — nothing to do.")
        return

    # Manual workflow_dispatch → send regardless of configured day/time
    is_manual = os.environ.get("GITHUB_EVENT_NAME", "") == "workflow_dispatch"

    today_name = datetime.datetime.utcnow().strftime("%A")
    print(f"Dispatch: {TODAY} ({today_name}), manual={is_manual}, "
          f"enabled={cfg.get('enabled')}, send_day={cfg.get('send_day')}, "
          f"recipients={cfg.get('recipients')}")

    if not should_send_today(cfg, force=is_manual):
        print("Not due — skipping.")
        return

    alerts = load_json("alerts.json")
    brief  = load_json("pipeline_monday_brief.json")

    if not alerts:
        print("ERROR: alerts.json missing — cannot build email.")
        sys.exit(1)

    html = build_email_html(alerts, brief)
    week = alerts.get("week_number", "")
    subject = f"Raisr Pipeline Brief — Week {week} · {TODAY}"
    sent = send_via_gmail(cfg["recipients"], subject, html)

    if sent:
        cfg["last_sent"] = datetime.datetime.utcnow().isoformat() + "Z"
        cfg["send_now"] = False
        save_email_config(cfg)
        print(f"Sent to {cfg['recipients']}. last_sent={cfg['last_sent']}")
    else:
        print("ERROR: send_via_gmail failed — check GMAIL_USER / GMAIL_APP_PASSWORD secrets.")
        sys.exit(1)


if __name__ == "__main__":
    main()
