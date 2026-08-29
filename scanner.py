import requests
import os

def main():
    url = "https://api.bitget.com/api/v2/mix/market/tickers?productType=USDT-FUTURES"
    response = requests.get(url, timeout=15)
    data = response.json().get("data", [])

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

    signals = []

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
                signals.append({
                    "symbol": sym,
                    "price": round(price, 6),
                    "change1h": round(change1h, 2),
                    "change4h": round(change4h, 2),
                    "volume": int(volume),
                    "vol_ratio": round(vol_ratio * 100)
                })
        except Exception:
            continue

    signals.sort(key=lambda x: -x["vol_ratio"])

    print("Тикер | Цена | Рост 1ч % | Рост 4ч % | Объём 1ч | Рост объёма %")
    if not signals:
        print("Сигналов нет")
    for s in signals:
        print(f"{s['symbol']} | {s['price']} | {s['change1h']} | {s['change4h']} | {s['volume']} | {s['vol_ratio']}")

if __name__ == "__main__":
    main()
