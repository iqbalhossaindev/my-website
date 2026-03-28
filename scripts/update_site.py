import json
import os
from datetime import datetime, timezone
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

COINGECKO_BASE = "https://api.coingecko.com/api/v3"
COINGECKO_KEY = os.getenv("COINGECKO_DEMO_API_KEY", "")

HEADERS = {}
if COINGECKO_KEY:
    HEADERS["x-cg-demo-api-key"] = COINGECKO_KEY

TICKER_COINS = [
    ("bitcoin", "BTC"),
    ("ethereum", "ETH"),
    ("binancecoin", "BNB"),
    ("solana", "SOL"),
    ("ripple", "XRP"),
    ("cardano", "ADA"),
]

def save_json(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

def fetch_market_data() -> dict:
    ids = ",".join([coin_id for coin_id, _ in TICKER_COINS])

    price_resp = requests.get(
        f"{COINGECKO_BASE}/simple/price",
        params={
            "ids": ids,
            "vs_currencies": "usd",
            "include_24hr_change": "true",
        },
        headers=HEADERS,
        timeout=30,
    )
    price_resp.raise_for_status()
    price_data = price_resp.json()

    prices = []
    for coin_id, symbol in TICKER_COINS:
        item = price_data.get(coin_id, {})
        prices.append(
            {
                "id": coin_id,
                "symbol": symbol,
                "price": item.get("usd"),
                "change_24h": item.get("usd_24h_change"),
            }
        )

    markets_resp = requests.get(
        f"{COINGECKO_BASE}/coins/markets",
        params={
            "vs_currency": "usd",
            "order": "market_cap_desc",
            "per_page": 100,
            "page": 1,
            "sparkline": "false",
            "price_change_percentage": "24h",
        },
        headers=HEADERS,
        timeout=30,
    )
    markets_resp.raise_for_status()
    markets = markets_resp.json()

    cleaned = []
    for item in markets:
        change = item.get("price_change_percentage_24h_in_currency")
        if change is None:
            continue
        cleaned.append(
            {
                "name": item.get("name"),
                "symbol": str(item.get("symbol", "")).upper(),
                "price": item.get("current_price"),
                "change_24h": change,
            }
        )

    bullish = sorted(cleaned, key=lambda x: x["change_24h"], reverse=True)[:5]
    bearish = sorted(cleaned, key=lambda x: x["change_24h"])[:5]

    return {
        "updated_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        "prices": prices,
        "bullish": bullish,
        "bearish": bearish,
    }

def load_existing_news() -> dict:
    news_file = DATA_DIR / "news.json"
    if news_file.exists():
        try:
            return json.loads(news_file.read_text(encoding="utf-8"))
        except Exception:
            pass

    return {
        "updated_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        "headlines": [],
        "articles": [],
    }

def main() -> None:
    market = fetch_market_data()
    save_json(DATA_DIR / "market.json", market)

    news = load_existing_news()
    save_json(DATA_DIR / "news.json", news)

if __name__ == "__main__":
    main()
