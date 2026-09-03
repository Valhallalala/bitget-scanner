import requests
import json
import os
from datetime import datetime

SHEET_ID = os.environ["OVERHEAT_SHEET_ID"]
CREDS = json.loads(os.environ["GDRIVE_CREDENTIALS"])

def get_access_token():
    import jwt
    import time

    now = int(time.time())
    payload = {
        "iss": CREDS["client_email"],
        "scope": "https://www.googleapis.com/auth/spreadsheets",
        "aud": "https://oauth2.googleapis.com/token",
        "iat": now,
        "exp": now + 3600
    }
    token = jwt.encode(payload, CREDS["private_key"], algorithm="RS256")

    r = requests.post("https://oauth2.googleapis.com/token", data={
        "grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer",
        "assertion": token
    }, timeout=15)

    print("Ответ Google:", r.text[:300])
    return r.json()["access_token"]

def update_sheet():
    token = get_access_token()
    sheet = "Лист1"
    url = f"https://sheets.googleapis.com/v4/spreadsheets/{SHEET_ID}/values/{sheet}!A1"

    data = [
        ["TEST", "1.23"],
    ]

    resp = requests.put(
        url,
        headers={"Authorization": f"Bearer {token}"},
        params={"valueInputOption": "RAW"},
        json={"range": f"{sheet}!A1", "majorDimension": "ROWS", "values": data},
        timeout=15
    )
    print("Статус записи:", resp.status_code)
    print("Ответ:", resp.text[:500])

if __name__ == "__main__":
    update_sheet()
