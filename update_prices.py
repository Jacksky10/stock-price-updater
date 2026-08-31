import os
from datetime import date, timedelta
from pathlib import Path

import pandas as pd
import requests

API_TOKEN = os.environ["EODHD_API_TOKEN"]

TICKERS = [
    "VGS.AU",
    "VGE.AU",
    "VISM.AU",
    "PMGOLD.AU",
    "ETPMAG.AU",
    "TSLA.US",
    "MSFT.US",
    "USDAUD.FOREX"
]

OUTPUT_FILE = Path(__file__).with_name("eodhd_daily_prices.csv")

# Look back far enough to cover weekends and market holidays.
start_date = date.today() - timedelta(days=10)

new_rows = []

for ticker in TICKERS:
    response = requests.get(
        f"https://eodhd.com/api/eod/{ticker}",
        params={
            "api_token": API_TOKEN,
            "fmt": "json",
            "from": start_date.isoformat(),
            "to": date.today().isoformat(),
            "order": "d",
        },
        timeout=30,
    )

    response.raise_for_status()
    records = response.json()

    if not records:
        print(f"No prices returned for {ticker}")
        continue

    # The first record is the latest available trading day.
    latest = records[0]

    # Add currency conversion ratio
    # USDAUD.FOREX = 1 USD expressed in AUD
    # All other assets remain at ratio 1
    if ticker == "USDAUD.FOREX":
        ratio = latest["close"]
    else:
        ratio = 1

    new_rows.append(
        {
            "Ticker": ticker,
            "Date": latest["date"],
            "Close": latest["close"],
            "Ratio": ratio,
        }
    )

new_data = pd.DataFrame(new_rows)

# Retain previously collected prices.
if OUTPUT_FILE.exists():
    existing_data = pd.read_csv(OUTPUT_FILE)
    all_data = pd.concat([existing_data, new_data], ignore_index=True)
else:
    all_data = new_data

# Prevent duplicate ticker/date rows if run more than once per day.
all_data = (
    all_data
    .drop_duplicates(subset=["Ticker", "Date"], keep="last")
    .sort_values(["Date", "Ticker"])
)

all_data.to_csv(OUTPUT_FILE, index=False)

print(f"\nUpdated: {OUTPUT_FILE}")
print(new_data.to_string(index=False))