import requests

def main():
    for sym in ["XRPUSDT", "ADAUSDT", "DOGEUSDT"]:
        url = "https://api.bitget.com/api/v2/mix/market/candles"
        params = {
            "symbol": sym,
            "granularity": "1D",
            "limit": 4
        }
        r = requests.get(url, params=params, timeout=15)
        js = r.json()
        data = js.get("data", [])

        print(sym, "| Статус:", r.status_code, "| Свечей:", len(data))
        if data:
            print("Последняя:", data[-1])
            print("Первая:", data[0])
        else:
            print("Ответ:", r.text[:300])
        print("-" * 40)

if __name__ == "__main__":
    main()
