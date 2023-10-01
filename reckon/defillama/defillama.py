import requests
from urllib.parse import quote
from datetime import datetime
from collections import defaultdict

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


def get_price(chain, token_id, date=None):
    """
    Get current or historical prices.

    Chain can be:
    - ethereum
    - avax
    - fantom
    """

    # If no date, then get the latest price
    if date is None:
        url = f"https://coins.llama.fi/prices/current/{chain}:{token_id}"
        response = requests.get(url)
        print(response.status_code)
        print(response.text)

    # Otherwise, get the price at the specified date
    else:
        timestamp = get_timestamp_from_date(date)
        url = f"https://coins.llama.fi/prices/historical/{timestamp}/{chain}:{token_id}"
        response = requests.get(url)
        print(response.status_code)
        print(response.text)


def get_prices(request_list):
    """
    Get a list of prices for a list of requests.

    The expected format for the request list is a list of
    [chain, token_id, date_str]. For example:

    [['avax', '0xb97ef9ef8734c71904d8002f8b6bc66dd9c48a6e', '2021-09-01 12:58:23'],
    ['ethereum', '0xD533a949740bb3306d119CC777fa900bA034cd52', '2021-08-04 14:58:23'],
    ['fantom', '0xf24bcf4d1e507740041c9cfd2dddb29585adce1e', '2021-12-09 01:18:45']]
    """
    request_dict = defaultdict(list)
    for request in request_list:
        chain = request[0]
        token_id = request[1]
        timestamp = get_timestamp_from_date(request[2])
        request_dict[f'{chain}:{token_id}'].append(timestamp)
    request = str(dict(request_dict))
    request = request.replace("'", '"')
    # print(request)
    url = f"https://coins.llama.fi/batchHistorical?coins={quote(request)}&searchWidth=600"
    # print(url)
    response = requests.get(url)
    json = response.json()
    prices_response = []
    if 'coins' in json:
        coins_dict = json['coins']
        for coin, coin_data in coins_dict.items():
            chain, token_id = coin.split(':')
            # print(coin_data)
            for prices in coin_data['prices']:
                timestamp = prices['timestamp']
                date = get_date_from_timestamp(timestamp)
                price = prices['price']
                confidence = prices['confidence'] if 'confidence' in prices else ''
                print(f"{date} {chain} {token_id} {price} {confidence}")
                prices_response.append([
                    date,
                    chain,
                    token_id,
                    price,
                    confidence
                ])

    return prices_response
    # priced = []
    # unpriced = []

    # prices_set = {(date, chain, token_id) for date, chain, token_id, _, _ in prices_response}

    # print(prices_set)
    # for req in request_list:
    #     print(req)
    #     chain, token_id, date = req
    #     if (date, chain, token_id) in prices_set:
    #         # Find the matching response to get the price
    #         matching_response = next(price for price in prices_response if (price[0], price[1], price[2]) == (date, chain, token_id))
    #         priced.append(req + [matching_response[3]])  # Append the price to the request
    #     else:
    #         unpriced.append(req)

    # print(priced)
    # print(unpriced)


if __name__ == "__main__":
    crv_token_id = "0xD533a949740bb3306d119CC777fa900bA034cd52"
    clev_token_id = "0x72953a5C32413614d24C29c84a66AE4B59581Bbf"
    beets_token_id = "0xf24bcf4d1e507740041c9cfd2dddb29585adce1e"
    time_token_id = "0xb54f16fb19478766a268f172c9480f8da1a7c9c3"
    # reqs = [
    #     ['ethereum', crv_token_id, get_timestamp_from_date("2021-08-04 14:58:23")],
    #     ['ethereum', clev_token_id, get_timestamp_from_date("2023-09-01 12:58:23")],
    #     ['fantom', beets_token_id, get_timestamp_from_date("2021-12-09 01:18:45")],
    #     ['avax', time_token_id, get_timestamp_from_date("2021-12-13 04:05:12")],

    # ]
    # for req in reqs:
    #     get_price_historical(req[0], req[1], req[2])

    # get_prices([
    #     ['ethereum', crv_token_id, '2021-08-04 14:58:23'],
    #     ['ethereum', '0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2', '2021-08-04 14:58:23'], # WETH
    #     ['ethereum', '0xaa0c3f5f7dfd688c6e646f66cd2a6b66acdbe434', '2023-10-01 11:51:11'],
    #     ['ethereum', crv_token_id, '2022-09-04 14:58:23'],
    #     ['ethereum', clev_token_id, '2023-09-01 12:58:23'],
    #     ['fantom', beets_token_id, '2021-12-09 01:18:45'],
    #     ['avax', time_token_id, '2021-12-13 04:05:12'],
    # ])

    price_reqs = [
        ['ethereum', crv_token_id, '2021-08-04 14:58:23'],
        ['ethereum', '0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2', '2021-08-04 14:58:23'], # WETH
        ['ethereum', '0xaa0c3f5f7dfd688c6e646f66cd2a6b66acdbe434', '2023-10-01 11:51:11'],
        ['ethereum', crv_token_id, '2022-09-04 14:58:23'],
        ['ethereum', clev_token_id, '2023-09-01 12:58:23'],
        ['fantom', beets_token_id, '2021-12-09 01:18:45'],
        ['avax', time_token_id, '2021-12-13 04:05:12'],
        ['ethereum', crv_token_id],
    ]

    for req in price_reqs:
        if len(req) == 3:
            get_price(req[0], req[1], req[2])
        else:
            get_price(req[0], req[1])