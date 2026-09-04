import requests
import json
import os
from datetime import datetime, timedelta, timezone

SHEET_ID = os.environ["SIGNALS_SHEET_ID"]
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

def get_sheet_data(spreadsheet_id, range_name):
    token = get_access_token()
    url = f"https://sheets.googleapis.com/v4/spreadsheets/{spreadsheet_id}/values/{range_name}"
    r = requests.get(url, headers={"Authorization": f"Bearer {token}"}, timeout=15)
    return r.json().get("values", [])

def update_sheet(rows):
    token = get_access_token()
    sheet = "Лист2"

    clear_url = f"https://sheets.googleapis.com/v4/spreadsheets/{SHEET_ID}/values/{sheet}!A:G"
    requests.post(clear_url + ":clear", headers={"Authorization": f"Bearer {token}"}, timeout=15)

    url = f"https://sheets.googleapis.com/v4/spreadsheets/{SHEET_ID}/values/{sheet}!A1"
    data = [
        ["Тикер", "Цена", "Сигнал", "Стоп", "ТП1", "ТП2", "Время"],
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
    # Читаем перегретые из первой таблицы
    overheat_id = os.environ["OVERHEAT_SHEET_ID"]
    overheat_data = get_sheet_data(overheat_id, "A2:A")

    if not overheat_data:
        print("Нет перегретых монет")
        return

    symbols = []
    for row in overheat_data:
        if row:
            symbols.append(row[0])

    signals = []

    for sym in symbols[:20]:
        try:
            c = requests.get(
                "https://api.bitget.com/api/v2/mix/market/candles",
                params={
                    "symbol": sym,
                    "granularity": "15m",
                    "limit": 6,
                    "productType": "USDT-FUTURES"
                },
                timeout=10
            ).json().get("data", [])

            if len(c) < 4:
                continue

            # Последние свечи
            last = c[0]
            prev = c[1]

            open_price = float(last[1])
            close_price = float(last[4])
            high_price = float(last[2])
            low_price = float(last[3])

            prev_close = float(prev[4])
            prev_high = float(prev[2])

            # Условия разворота
            is_bearish = close_price < open_price
            upper_wick = (high_price - max(open_price, close_price)) / high_price > 0.001
            rejected_high = high_price >= prev_high * 1.005
            pullback = close_price < prev_close * 0.995

            if is_bearish and (rejected_high or upper_wick) and pullback:
                stop = round(high_price * 1.01, 6)
                tp1 = round(close_price * 0.97, 6)
                tp2 = round(close_price * 0.94, 6)

                signals.append([
                    sym,
                    round(close_price, 6),
                    "Разворот",
                    stop,
                    tp1,
                    tp2,
                    (datetime.now(timezone.utc) + timedelta(hours=5)).strftime("%H:%M:%S")
                ])
        except Exception:
            continue

    update_sheet(signals)
    print("Сигналов:", len(signals))

if __name__ == "__main__":
    main()
