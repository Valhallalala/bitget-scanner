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
    return r.json()["access_token"]

def update_sheet(rows):
    token = get_access_token()
    sheet = "Лист1"
    url = f"https://sheets.googleapis.com/v4/spreadsheets/{SHEET_ID}/values/{sheet}!A1"

    data = [
        ["Тикер", "Цена", "Рост 24ч, %", "Рост 3д, %", "Фондинг, %", "Объём 24ч, $", "Обновлено"],
        *rows
    ]

    requests.put(
        url,
        headers={"Authorization": f"Bearer {token}"},
        params={"valueInputOption": "RAW"},
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
        try:
            price = float(item.get("lastPr", 0))
            change24h = float(item.get("change24h", 0)) * 100
            funding = float(item.get("fundingRate", 0)) * 100
            vol = float(item.get("usdtVolume", item.get("quoteVolume", 0)))
        except:
            continue
        if price <= 0:
            continue

        candidates.append((sym, price, change24h, funding, vol))

        candidates = candidates

    rows = []

    for sym, price, change24h, funding, vol in candidates:
        try:
            c = requests.get(
                "https://api.bitget.com/api/v2/mix/market/candles",
                params={"symbol": sym, "granularity": "1D", "limit": 4},
                timeout=10
            ).json().get("data", [])
            if len(c) < 4:
                continue

            price3d = float(c[3][4])
            change3d = (price - price3d) / price3d * 100

            if (change24h >= 5 or change3d >= 10) and funding > 0.001:
                rows.append([
                    sym,
                    round(price, 6),
                    round(change24h, 2),
                    round(change3d, 2),
                    round(funding, 4),
                    int(vol),
                    datetime.utcnow().strftime("%H:%M:%S")
                ])
        except Exception:
            continue

    rows.sort(key=lambda x: -x[4])
    update_sheet(rows)
    print("Обновлено строк:", len(rows))

if __name__ == "__main__":
    main()
