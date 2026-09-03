import requests

def main():
    url = "https://api.bitget.com/api/v2/mix/market/tickers?productType=USDT-FUTURES"
    data = requests.get(url, timeout=15).json().get("data", [])

    best = []
    for item in data:
        sym = item.get("symbol", "")
        if "USDT" not in sym:
            continue
        try:
            change = float(item.get("change24h", 0)) * 100
            funding = float(item.get("fundingRate", 0)) * 100
            vol = float(item.get("usdtVolume", 0))
        except:
            continue

        if funding > 0.001:
            best.append((sym, change, funding, vol))

    best.sort(key=lambda x: -x[2])

    print("Монеты с фондингом > 0.001%:")
    for sym, change, funding, vol in best[:15]:
        print(f"{sym} | Рост 24ч: {change:.2f}% | Фондинг: {funding:.4f}% | Объём: {vol:.0f}")

if __name__ == "__main__":
    main()
