import datetime
import json
import os
import random
import requests
import time
import reckon.utils as utils
from reckon.constants import COINGECKO_ID_EXPLICIT, PRICE_CACHE_FILE, COINGECKO_COINS_LIST_FILE

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
        matches = [x['id'] for x in COINGECKO_ID_LIST if x['symbol'] == symbol.lower()]
        if len(matches) == 1:
            # print(f'LIST {date} | {purchase_token} => {matches[0]}')
            COINGECKO_ID_EXPLICIT[symbol.lower()] = matches[0]
            return matches[0]
        else:
            print(f'ERROR: MORE THAN 1 COIN ID FOR {symbol} => {matches}')
    else:
        print(f'ERROR: NO COIN ID FOUND FOR {symbol}')
        print(f'  You can manually set an entry for {symbol} in reckon.constants.COINGECKO_ID_EXPLICIT')
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
    if type(date) != datetime.datetime:
        raise Exception("Date is not a valid datetime object")

    if os.path.isfile(PRICE_CACHE_FILE):
        with open(PRICE_CACHE_FILE, 'r') as f:
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
    cached_price = get_cached_historical_price(symbol, date)

    if cached_price == None:
        with open(PRICE_CACHE_FILE, 'a') as f:
            date_added = datetime.datetime.now().strftime('%Y-%m-%d')
            f.write(f"{date.strftime('%Y-%m-%d')},{symbol},{price},{date_added},{source}\n")
    else:
        # print(f'WARN: Entry for {date}|{symbol}|{price} already exists')
        pass


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
    if type(date) != datetime.datetime:
        raise Exception("Date is not a valid datetime object")

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
    sleep_time = random.randrange(3000, 5000)
    time.sleep(sleep_time/1000)
    print(f'Throttle {sleep_time} request price {url}', end = ' => ')
    response = requests.get(url)
    price_data = json.loads(response.text)
    price = utils.get_nested_dict(price_data, 'market_data.current_price.usd')

    if price != None and price != '':
        save_historical_price(symbol, date, price)
        print(f'{price}')
        return float(price)
    else:
        print(f'No price found')
        return None


def clean_cache():
    """
    Maintenance function to clean up the PRICE_CACHE_FILE.

    Cleans cache by: 1) Removing duplicates, 2) Sorting
    """
    cache = []
    with open(PRICE_CACHE_FILE, 'r') as f:
        for line in f:
            date, symbol, price, date_added, source = line.rstrip().split(',')
            if [date,symbol] not in cache:
                cache.append([date,symbol,price,date_added,source])
            else:
                print(f'ERROR: Discarding duplicate cache result for {date}|{symbol}|{price}|{source}')
    cache.sort()
    utils.list_to_csv(cache, PRICE_CACHE_FILE)


clean_cache()

if __name__ == '__main__':
    # save_historical_price('btc', datetime.datetime(2021, 2, 7), 100.0)
    # historical_price('cvx', 'Not a date')
    # historical_price('btc', datetime.datetime(2021, 2, 7))
    # print(cached_historical_price('btc', datetime.datetime(2021, 2, 7)))
    # historical_price('eth', datetime.datetime(2021, 3, 31))
    # historical_price('crv', datetime.datetime(2021, 1, 12))
    # historical_price('made-up-doesnt-exist', '01-12-2022')
    # clean_cache()
    pass