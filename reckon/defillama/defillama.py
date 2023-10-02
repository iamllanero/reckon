from config import DEFILLAMA_CACHE_OUTPUT, DEFILLAMA_MISSING_OUTPUT
from datetime import datetime
import csv
import os
import requests
import sys


PRICE_CACHE = []
MISSING_CACHE = []
HEADERS = ["date", "chain", "symbol", "token_id", "price"]


def get_timestamp_from_date(date_str, date_format="%Y-%m-%d %H:%M:%S"):
    """Convert a date string to a timestamp."""
    dt = datetime.strptime(date_str, date_format)
    timestamp = int(dt.timestamp())
    return timestamp


def get_date_from_timestamp(timestamp, date_format="%Y-%m-%d %H:%M:%S"):
    """Convert a timestamp to a date string."""
    dt = datetime.fromtimestamp(timestamp)
    date_str = dt.strftime(date_format)
    return date_str


def check_cache(date, chain, symbol, token_id):
    """Check the cache for a price."""
    for price in PRICE_CACHE:
        if price[0] == date and \
            price[1] == chain and \
            price[3] == token_id:
            return price[4]
    return None


def is_known_missing(date, chain, symbol, token_id) -> bool:
    """Check the missing cache for a price."""
    for price in MISSING_CACHE:
        if price[0] == date and \
            price[1] == chain and \
            price[3] == token_id:
            return True
    return False


def clean_cache(file_path):
    with open(file_path, 'r') as f:
        reader = csv.reader(f)
        data = list(reader)
    
    # If the CSV has headers, separate them from the data
    headers = data[0]
    data = data[1:]
    
    # De-duplicate by converting to a set of tuples and then back to a list of lists
    data = [list(item) for item in set(tuple(row) for row in data)]
    
    # Sort by date, chain, symbol, and token_id
    data.sort(key=lambda x: (x[0], x[1], x[2], x[3]))
    
    # Write the sorted list back to the CSV file
    with open(file_path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(headers)  # Write the headers back
        writer.writerows(data)


def save_cache(date, chain, symbol, token_id, price):
    """Save a price to the cache."""
    PRICE_CACHE.append([
        date,
        chain,
        symbol,
        token_id,
        price
    ])
    with open(DEFILLAMA_CACHE_OUTPUT, "a", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(PRICE_CACHE[-1])


def save_missing(date, chain, symbol, token_id):
    """Save a missing price to the cache."""
    MISSING_CACHE.append([
        date,
        chain,
        symbol,
        token_id,
        ''
    ])
    with open(DEFILLAMA_MISSING_OUTPUT, "a", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([date, chain, symbol, token_id, ''])


def get_price(date, chain, symbol, token_id):
    """
    Get historical prices.

    Chain can be:
    - ethereum
    - avax
    - fantom
    """
    price = check_cache(date, chain, symbol, token_id)
    if price is None and \
        not is_known_missing(date, chain, symbol, token_id):

        price = _get_price(date, chain, symbol, token_id)
        if price is not None:
            save_cache(date, chain, symbol, token_id, price)
        else:
            save_missing(date, chain, symbol, token_id)

    return price


def _get_price(date, chain, symbol, token_id):

    timestamp = get_timestamp_from_date(date)
    url = f"https://coins.llama.fi/prices/historical/{timestamp}/{chain}:{token_id}"
    print(f"GET {url} ({symbol})", end=" => ")
    response = requests.get(url)
    if response.status_code != 200:
        print(response.status_code)
        sys.exit(1, f"ERROR: {response.status_code} for {date} {chain} {symbol} {token_id}")
    if "coins" in response.json():
        coins = response.json()["coins"]
        for k,v in coins.items():
            print(f"{response.status_code} / Price: {v['price']}")
            return v["price"]
    print(f"{response.status_code} / No price found")
    return None

if os.path.exists(DEFILLAMA_CACHE_OUTPUT):
    clean_cache(DEFILLAMA_CACHE_OUTPUT)
    with open(DEFILLAMA_CACHE_OUTPUT, "r") as f:
        next(f)
        reader = csv.reader(f)
        for row in reader:
            PRICE_CACHE.append(row)
else:
    with open(DEFILLAMA_CACHE_OUTPUT, "w") as f:
        writer = csv.writer(f)
        writer.writerow(HEADERS)

if os.path.exists(DEFILLAMA_MISSING_OUTPUT):
    clean_cache(DEFILLAMA_MISSING_OUTPUT)
    with open(DEFILLAMA_MISSING_OUTPUT, "r") as f:
        next(f)
        reader = csv.reader(f)
        for row in reader:
            MISSING_CACHE.append(row)
else:
    with open(DEFILLAMA_MISSING_OUTPUT, "w") as f:
        writer = csv.writer(f)
        writer.writerow(HEADERS)
