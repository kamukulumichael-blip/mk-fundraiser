#!/usr/bin/env python3
"""
One-time MS365 authorisation for Raisr Research Bot.
Run locally:  python3 setup_ms365.py
Then copy the refresh token printed at the end into GitHub Secrets as MS_REFRESH_TOKEN.
"""

import requests, time

TENANT_ID = "4652dfab-8b3b-4968-aef1-d50842fdff5f"
CLIENT_ID = "5e6fd45f-e90d-4869-a7fb-42a81eaad28d"
SCOPES    = "Mail.ReadBasic Calendars.Read offline_access"

resp = requests.post(
    f"https://login.microsoftonline.com/{TENANT_ID}/oauth2/v2.0/devicecode",
    data={"client_id": CLIENT_ID, "scope": SCOPES}
)
if resp.status_code != 200:
    print(f"Error starting device flow: {resp.status_code} {resp.text}")
    raise SystemExit(1)

data = resp.json()
print("\n" + "=" * 60)
print("STEP 1 — Open this URL in your browser:")
print(f"         {data['verification_uri']}")
print(f"\nSTEP 2 — Enter this code when prompted:  {data['user_code']}")
print(f"\nSign in as mkamukulu@learnimpact.org")
print("=" * 60)
print(f"\nWaiting (expires in {data['expires_in'] // 60} min)...", end="", flush=True)

interval    = data.get("interval", 5)
device_code = data["device_code"]

while True:
    time.sleep(interval)
    t = requests.post(
        f"https://login.microsoftonline.com/{TENANT_ID}/oauth2/v2.0/token",
        data={
            "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
            "client_id":   CLIENT_ID,
            "device_code": device_code,
        }
    ).json()

    if "access_token" in t:
        print("\n\n✓ Authorised!\n")
        print("=" * 60)
        print("Add this to GitHub Secrets as:  MS_REFRESH_TOKEN")
        print("=" * 60)
        print(t["refresh_token"])
        print("=" * 60)
        print("\nDone. You can close this terminal.")
        break
    elif t.get("error") == "authorization_pending":
        print(".", end="", flush=True)
    elif t.get("error") == "slow_down":
        interval += 5
        print(".", end="", flush=True)
    else:
        print(f"\n\nFailed: {t}")
        break
