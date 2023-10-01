import requests
from urllib.parse import quote
from datetime import datetime
from collections import defaultdict

def get_timestamp_from_date(date_str, date_format="%Y-%m-%d %H:%M:%S"):
    """
    Convert a date string to a timestamp.

    Args:
    - date_str (str): The date string to convert.
    - date_format (str, optional): The format of the date string. Defaults to "%Y-%m-%d %H:%M:%S".

    Returns:
    - int: The timestamp corresponding to the date string.
    """
    dt = datetime.strptime(date_str, date_format)
    timestamp = int(dt.timestamp())
    return timestamp


def get_price_historical(chain, token_id, timestamp):
    """
    Get historical prices.

    Chain can be:
    - ethereum
    - avax
    - fantom
    """
    url = f"https://coins.llama.fi/prices/historical/{timestamp}/{chain}:{token_id}"
    response = requests.get(url)
    print(response.status_code)
    print(response.json())


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
        chain = "ethererum" if chain == "eth" else chain
        token_id = request[1]
        timestamp = get_timestamp_from_date(request[2])
        request_dict[f'{chain}:{token_id}'].append(timestamp)
    json = str(dict(request_dict))
    json = json.replace("'", '"')
    print(json)
    # json = '{"avax:0xb97ef9ef8734c71904d8002f8b6bc66dd9c48a6e": [1666876743, 1666862343]}'
    url = f"https://coins.llama.fi/batchHistorical?coins={quote(json)}&searchWidth=600"
    print(url)
    response = requests.get(url)
    print(response.status_code)
    print(response.text)


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

    get_prices([
        ['ethereum', crv_token_id, '2021-08-04 14:58:23'],
        ['ethereum', '0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2', '2021-08-04 14:58:23'], # WETH
        ['ethereum', clev_token_id, '2023-09-01 12:58:23'],
        ['fantom', beets_token_id, '2021-12-09 01:18:45'],
        ['avax', time_token_id, '2021-12-13 04:05:12'],
    ])