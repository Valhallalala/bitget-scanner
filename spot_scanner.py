import requests
import json
import os
from datetime import datetime, timedelta, timezone

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
    sheet = "Лист3"

    clear_url = f"https://sheets.googleapis.com/v4/spreadsheets/{SHEET_ID}/values/{sheet}!A:F"
    requests.post(clear_url + ":clear", headers={"Authorization": f"Bearer {token}"}, timeout=15)

    url = f"https://sheets.googleapis.com/v4/spreadsheets/{SHEET_ID}/values/{sheet}!A1"
    data = [
        ["Тикер", "Цена", "Диапазон, %", "Рост объёма, %", "EMA30", "Обновлено"],
        *rows
    ]

    requests.put(
        url,
        headers={"Authorization": f"Bearer {token}"},
        params={"valueInputOption": "RAW"},
        json={"range": f"{sheet}!A1", "majorDimension": "ROWS", "values": data},
        timeout=15
    )

def ema(values, period):
    k = 2 / (period + 1)
    result = []
    prev = float(values[0])
    for v in values:
        prev = float(v) * k + prev * (1 - k)
        result.append(prev)
    return result

def main():
    url = "https://api.bitget.com/api/v2/spot/market/tickers"
    data = requests.get(url, timeout=15).json().get("data", [])

    candidates = []
    for item in data:
        sym = item.get("symbol", "")
        if "USDT" not in sym:
            continue
        if not sym.replace("USDT", "").isalnum():
            continue
        if sym.startswith("R"):
            continue

        excluded = ["USDTEUR","USDCUSDT","FDUSDUSDT","TUSDUSDT","DAIUSDT","EURUSDT","USDPUSDT"]
        if sym in excluded:
            continue

        try:
            price = float(item.get("lastPr", item.get("close", 0)))
            base_vol = float(item.get("baseVolume", item.get("usdtVolume", 0)))
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
            c = requests.get(
                "https://api.bitget.com/api/v2/spot/market/candles",
                params={"symbol": sym, "granularity": "1h", "limit": 35},
                timeout=10
            ).json().get("data", [])

            if len(c) < 35:
                continue

            closes = [float(x[4]) for x in reversed(c)]
            highs = [float(x[2]) for x in reversed(c)]
            lows = [float(x[3]) for x in reversed(c)]
            volumes = [float(x[5]) for x in reversed(c)]

            last_close = closes[-1]
            prev_close = closes[-2]

            ema30 = ema(closes, 30)
            last_ema = ema30[-1]
            prev_ema = ema30[-2]

            # Пересечение EMA30 снизу вверх
            if not (prev_close < prev_ema and last_close > last_ema):
                continue

            # Узкий диапазон за 6 часов
            recent_high = max(highs[-6:])
            recent_low = min(lows[-6:])
            range_pct = (recent_high - recent_low) / recent_low * 100

            if range_pct > 3.0:
                continue

            # Рост объёма
            current_vol = volumes[-1]
            avg_vol = sum(volumes[-21:-1]) / 20
            if avg_vol <= 0:
                continue
            vol_ratio = current_vol / avg_vol

            if vol_ratio < 1.5:
                continue

            rows.append([
                sym,
                round(last_close, 6),
                round(range_pct, 2),
                round(vol_ratio * 100),
                round(last_ema, 6),
                (datetime.now(timezone.utc) + timedelta(hours=5)).strftime("%H:%M:%S")
            ])
        except Exception:
            continue

    rows.sort(key=lambda x: -x[3])
    update_sheet(rows)
    print("Обновлено строк:", len(rows))

if __name__ == "__main__":
    main()
