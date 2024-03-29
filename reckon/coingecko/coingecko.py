import csv
from datetime import datetime, timezone
import json
import os
import requests
import time
# import utils
from config import (
    COINGECKO_CACHE_OUTPUT,
    COINGECKO_COINS_LIST_FILE,
    COINGECKO_ID_EXPLICIT,
    COINGECKO_MISSING_OUTPUT,
    COINGECKO_TOML,
    PRICE_MANUAL_FILE,
)

COINGECKO_ID_LIST = json.load(open(COINGECKO_COINS_LIST_FILE))
COINGECKO_IDS = [elem['symbol'] for elem in COINGECKO_ID_LIST]


def get_coin_id(symbol):
    """
    Gets the CoinGecko coin ID that used for API queries. Refer to the docs at
    https://www.coingecko.com/en/api/documentation for /coins/list.

    Note that this function references the file in COINGECKO_ID_LIST. It can be
    manually generated via the documentation. There is not currently support to
    do it automatically.

    Parameters:
        symbol (str): ERC 20 token symbol

    Returns:
        string: CG coin ID

    """
    if symbol.lower() in COINGECKO_ID_EXPLICIT:
        # print(f'PRELIST {date} | {purchase_token} => {COINGECKO_ID_DICT[purchase_token]}')
        return COINGECKO_ID_EXPLICIT[symbol.lower()]
    elif symbol.lower() in COINGECKO_IDS:
        matches = [x['id']
                   for x in COINGECKO_ID_LIST if x['symbol'] == symbol.lower()]
        if len(matches) == 1:
            # print(f'LIST {date} | {purchase_token} => {matches[0]}')
            COINGECKO_ID_EXPLICIT[symbol.lower()] = matches[0]
            return matches[0]
        else:
            print(f'ERROR: MORE THAN 1 COIN ID FOR {symbol} => {matches}')
    else:
        print(f'ERROR: NO COIN ID FOUND FOR {symbol}')
        print(
            f'  You can manually set an entry for {symbol} in {COINGECKO_TOML}')
        print(f'  "{symbol}": "<<VALID COIN ID>>",')
    # print(f'Lookup {coin_id}')
    return None


def get_cached_historical_price(symbol: str, date: datetime):
    """
    Tries to get the historical price from the cache file.

    This function raises an Exception if the datetime object is not valid.

    This function returns None if the symbol is not found in the cache.

    Parameters:
        symbol (str): ERC0-20 token symbol (i.e. ETH, CRV, CVX)
        date (datetime): Python datetime object

    Returns:
        float: Price
    """
    # Verify parameters
    if type(date) != datetime:
        raise Exception("Date is not a valid datetime object")
    date = date.replace(tzinfo=timezone.utc)

    # if os.path.isfile(PRICE_MANUAL_FILE):
    #     with open(PRICE_MANUAL_FILE, 'r') as f:
    #         for line in f:
    #             ldate, lsymbol, lprice, ldate_added, lsource = line.rstrip().split(',')
    #             if ldate == date.strftime("%Y-%m-%d") and \
    #                     lsymbol.lower() == symbol.lower() and \
    #                     lprice != '':
    #                 return float(lprice)

    if os.path.isfile(COINGECKO_CACHE_OUTPUT):
        with open(COINGECKO_CACHE_OUTPUT, 'r') as f:
            for line in f:
                ldate, lsymbol, lprice, ldate_added, lsource = line.rstrip().split(',')
                if ldate == date.strftime("%Y-%m-%d") and \
                        lsymbol.lower() == symbol.lower() and \
                        lprice != '':
                    # print(f'Cache hit for {date.strftime("%Y-%m-%d")}:{symbol}:{price}')
                    return float(lprice)

    return None


def save_historical_price(symbol: str,
                          date: datetime,
                          price: float,
                          source: str = "Coingecko"):
    """
    Saves the price data to PRICE_CACHE_FILE if it doesn't already exist.

    Parameters:
        symbol (str): ERC-20 token symbol
        date (datetime): Date of the price
        price (float): Price at close of the date
        source (str): Optional; default is Coingecko; source of the price quote
    """
    date = date.replace(tzinfo=timezone.utc)
    cached_price = get_cached_historical_price(symbol, date)

    if cached_price == None:
        with open(COINGECKO_CACHE_OUTPUT, 'a') as f:
            date_added = datetime.utcnow().strftime('%Y-%m-%d')
            f.write(
                f"{date.strftime('%Y-%m-%d')},{symbol},{price},{date_added},{source}\n")
    else:
        # print(f'WARN: Entry for {date}|{symbol}|{price} already exists')
        pass


def save_missing_price(symbol: str, date: datetime):
    """
    Saves the price data to PRICE_MISSING_FILE if it doesn't already exist.

    Parameters:
        symbol (str): ERC-20 token symbol
        date (datetime): Date of the price
    """
    date = date.replace(tzinfo=timezone.utc)
    # print(f"Saving {symbol} price for {date} to {PRICE_MISSING_OUTPUT}")
    with open(COINGECKO_MISSING_OUTPUT, 'a') as f:
        date_added = datetime.utcnow().strftime('%Y-%m-%d')
        f.write(f"{date.strftime('%Y-%m-%d')},{symbol},?,{date_added},Missing\n")


def get_historical_price(symbol: str, date: datetime):
    """
    Gets the historical price from CoinGecko or cached result.

    This function raises an Exception if the datetime object is not valid.

    This function returns None if: 1) the symbol is not found, 2) there are
    multiple coin ids found for the symbol, or 3) the historical price is
    missing from CG.

    Parameters:
        symbol (str): ERC0-20 token symbol (i.e. ETH, CRV, CVX)
        date (datetime): Python datetime object

    Returns:
        float: Price
    """

    # Verify parameters
    if type(date) != datetime:
        raise Exception("Date is not a valid datetime object")
    date = date.replace(tzinfo=timezone.utc)

    # Check for cached price and if present return it
    price = get_cached_historical_price(symbol, date)
    if price != None:
        return float(price)

    # Check if CoinGecko has the symbol listed; if not return None
    coin_id = get_coin_id(symbol)
    if coin_id == None:
        print(f'No historical price for {date} | {symbol}')
        return None

    # Make throttled request to CoinGecko API
    url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/history?date={date.strftime('%d-%m-%Y')}&localization=false"

    fetched = False
    while not fetched:
        print(
            f"GET https://api.coingecko.com/api/v3/coins/{coin_id}/history?date={date.strftime('%d-%m-%Y')}", end=" => ")
        response = requests.get(url)
        if response.status_code == 200:
            fetched = True
            try:
                # price = float(utils.get_nested_dict(
                #     response.json(), 'market_data.current_price.usd'))
                price = response.json()['market_data']['current_price']['usd']
                save_historical_price(symbol, date, price)
                print(f"200 OK")
                time.sleep(3)
                return price
            except:
                print(f"200 OK / ERROR: No price for {date} | {symbol}")
                # print(response.json['market_data']['current_price'])
                save_missing_price(symbol, date)
                time.sleep(3)
                return None
        elif response.status_code == 429:
            print(f"429 Too Many Requests / Sleeping for 60 seconds")
            time.sleep(60)
        elif response.status_code == 404:
            print(f"404 Not Found")
            save_missing_price(symbol, date)
            time.sleep(3)
            return None
        else:
            print(f"ERROR: {response.status_code}")
            print(response.text)
            save_missing_price(symbol, date)
            time.sleep(3)
            return None


def clean_cache(file_path):
    """
    Maintenance function to clean up the PRICE_CACHE_FILE.

    Cleans cache by: 1) Removing duplicates, 2) Sorting
    """
    cache = []
    if os.path.isfile(file_path):
        with open(file_path, 'r') as f:
            for line in f:
                date, symbol, price, date_added, source = line.rstrip().split(',')
                if [date, symbol] not in cache:
                    cache.append([date, symbol, price, date_added, source])
                else:
                    print(
                        f'ERROR: {file_path}: Discarding duplicate cache result for {date}|{symbol}|{price}|{source}')
    cache.sort()
    with open(file_path, 'w', newline='') as csvfile:
        csvwriter = csv.writer(csvfile)
        csvwriter.writerows(cache)


def clean_caches():
    clean_cache(COINGECKO_CACHE_OUTPUT)
    clean_cache(COINGECKO_MISSING_OUTPUT)


clean_caches()


if __name__ == '__main__':
    clean_caches()