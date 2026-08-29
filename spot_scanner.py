import requests

def main():
    url = "https://api.bitget.com/api/v2/spot/market/tickers"
    response = requests.get(url, timeout=15)
    data = response.json().get("data", [])

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

    signals = []

    for sym, price, base_vol in candidates:
        try:
            c = requests.get(
                "https://api.bitget.com/api/v2/spot/market/candles",
                params={"symbol": sym, "granularity": "1h", "limit": 20},
                timeout=10
            ).json().get("data", [])
            if len(c) < 10:
                continue

            volume = float(c[0][5])
            avg_vol = sum(float(x[5]) for x in c[1:]) / (len(c) - 1)
            if avg_vol <= 0:
                continue

            vol_ratio = volume / avg_vol
            prev_price = float(c[1][4])
            change1h = (price - prev_price) / prev_price * 100

            if vol_ratio >= 2.0 and volume >= 300000:
                signals.append({
                    "symbol": sym,
                    "price": round(price, 6),
                    "volume": int(volume),
                    "vol_ratio": round(vol_ratio * 100),
                    "change1h": round(change1h, 2)
                })
        except Exception:
            continue

    signals.sort(key=lambda x: -x["vol_ratio"])

    print("Тикер | Цена | Объём 1ч | Рост объёма % | Изм. цены 1ч %")
    if not signals:
        print("Сигналов нет")
    for s in signals:
        print(f"{s['symbol']} | {s['price']} | {s['volume']} | {s['vol_ratio']} | {s['change1h']}")

if __name__ == "__main__":
    main()
