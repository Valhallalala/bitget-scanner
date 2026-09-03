import requests

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
            change24h = float(item.get("change24h", 0)) * 100
            funding = float(item.get("fundingRate", 0)) * 100
        except:
            continue

        if (change24h >= 5 and funding > 0.001):
            candidates.append((sym, change24h, funding))

    print("Кандидатов после 24ч+фондинг:", len(candidates))
    for sym, change, funding in candidates[:20]:
        print(f"{sym} | 24ч: {change:.2f}% | Фондинг: {funding:.4f}%")

if __name__ == "__main__":
    main()
