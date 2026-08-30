import requests
import json
import os
from datetime import datetime

SHEET_ID = os.environ["SPREADSHEET_ID"]
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
        "grant_type": "urn:ietf:params:oauth:grant_type:jwt-bearer",
        "assertion": token
    }, timeout=15)
    resp = r.json()
    if "access_token" not in resp:
        print("Ответ Google:", resp)
        raise SystemExit(1)
    return resp["access_token"]

def update_sheet(rows):
    token = get_access_token()
    sheet = "Лист1"
    url = f"https://sheets.googleapis.com/v4/spreadsheets/{SHEET_ID}/values/{sheet}!A1"

    data = [
        ["Тикер", "Цена", "Рост 1ч, %", "Рост 4ч, %", "Объём 1ч, $", "Рост объёма, %", "Обновлено"],
        *rows
    ]

    requests.put(
        url,
        headers={"Authorization": f"Bearer {token}"},
        json={"range": f"{sheet}!A1", "majorDimension": "ROWS", "values": data},
        timeout=15
    )

def main():
    url = "https://api.bitget.com/api/v2/mix/market/tickers?productType=USDT-FUTURES"
    data = requests.get(url, timeout=15).json().get("data", [])

    candidates = []
    for item in data:
        sym = item.get("symbol", "")
        if "USDT" not in sym:
            continue
        if not sym.replace("USDT", "").isalnum():
            continue
        try:
            price = float(item.get("lastPr", 0))
            base_vol = float(item.get("baseVolume", item.get("baseCoinVolume", 0)))
        except:
            continue
        if price <= 0 or base_vol <= 0:
            continue
        candidates.append((sym, price, base_vol))

    candidates.sort(key=lambda x: -x[2])
    candidates = candidates[:150]

    rows = []

    for sym, price, base_vol in candidates:
        try:
            c1 = requests.get(
                "https://api.bitget.com/api/v2/mix/market/candles",
                params={"symbol": sym, "granularity": "1h", "limit": 5},
                timeout=10
            ).json().get("data", [])
            if len(c1) < 3:
                continue

            prev1 = float(c1[1][4])
            change1h = (price - prev1) / prev1 * 100
            volume = float(c1[0][5])

            avg_vol = sum(float(c[5]) for c in c1[1:]) / (len(c1) - 1)
            if avg_vol <= 0:
                continue
            vol_ratio = volume / avg_vol

            c4 = requests.get(
                "https://api.bitget.com/api/v2/mix/market/candles",
                params={"symbol": sym, "granularity": "4h", "limit": 2},
                timeout=10
            ).json().get("data", [])
            if len(c4) < 2:
                continue

            prev4 = float(c4[1][4])
            change4h = (price - prev4) / prev4 * 100

            overheat1h = 2 <= change1h <= 15
            overheat4h = 3 <= change4h <= 25
            strong_volume = volume >= 500000 and vol_ratio >= 2

            if (overheat1h or overheat4h) and strong_volume:
                rows.append([
                    sym,
                    round(price, 6),
                    round(change1h, 2),
                    round(change4h, 2),
                    int(volume),
                    round(vol_ratio * 100),
                    datetime.utcnow().strftime("%H:%M:%S")
                ])
        except Exception:
            continue

    rows.sort(key=lambda x: -x[5])
    update_sheet(rows)
    print("Обновлено строк:", len(rows))

if __name__ == "__main__":
    main()
if __name__ == "__main__":
    main()
