import requests

def main():
    url = "https://api.bitget.com/api/v2/mix/market/candles"
    params = {
        "symbol": "牛来USDT",
        "granularity": "1D",
        "limit": 4
    }
    r = requests.get(url, params=params, timeout=15)
    print("Статус:", r.status_code)
    print("Ответ:", r.text[:500])

if __name__ == "__main__":
    main()
