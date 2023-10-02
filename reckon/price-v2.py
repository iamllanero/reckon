import csv
import defillama as dl
import coingecko as cg
from datetime import datetime
from config import TXNS_PRICE_REQ_OUTPUT, PRICE_REQ_OUTPUT

TOKEN_SYMBOL_ID = {
    'ada': '',
    'arbitrum:arb': '0x912CE59144191C1204E64559FE8253a0e49E6548',
    'arbitrum:eth': '0x82af49447d8a07e3bd95bd0d56f35241523fbab1', # weth
    'algo': '',
    'avax:avax': '0xB31f66AA3C1e785363F0875A1B74E27b85FD66c7', # wavax
    'bch': '',
    'bchsv': '',
    'bsv': '',
    'ethereum:aave': '0x7Fc66500c84A76Ad7e9c93437bFc5Ac33E2DDaE9',
    'ethereum:avax': '0x85f138bfEE4ef8e540890CFb48F620571d67Eda3', # wavax
    'ethereum:bnb': '0x418D75f65a02b3D53B2418FB8E1fe493759c7605', # wbnb
    'ethereum:btc': '0x2260FAC5E5542a773Aa44fBCfeDf7C193bc2C599', # wbtc
    'ethereum:crv': '0xD533a949740bb3306d119CC777fa900bA034cd52',
    'ethereum:eth': '0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2', # weth
    'ethereum:forth': '0x77FbA179C79De5B7653F68b5039Af940AdA60ce0',
    'ethereum:ftm': '0x4E15361FD6b4BB609Fa63C81A2be19d873717870',
    'ethereum:grt': '0xc944E90C64B2c07662A292be6244BDf05Cda44a7',
    'ethereum:link': '0x514910771AF9Ca656af840dff83E8264EcF986CA',
    'ethereum:luna': '0xbd31EA8212119f94A611FA969881CBa3EA06Fa3d', # wluna
    'ethereum:nu': '0x4fE83213D56308330EC302a8BD641f1d0113A4Cc',
    'ethereum:shib': '0x95aD61b0a150d79219dCF64E1E6Cc01f0B64C4cE',
    'ethereum:spell': '0x090185f2135308BaD17527004364eBcC2D37e5F6',
    'fantom:ftm': '0x21be370d5312f44cb42ce377bc9b8a0cef1a4c83', #wftm
    'xlm': '',
}


def reset_prices_file():
    """
    Reset the prices file to just the header.
    """

    with open(PRICE_REQ_OUTPUT, "w", newline="") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["date", "chain", "symbol", "token_id", "price", "source"])


def lookup_token_id(chain, symbol):

    lookup = f"{chain.lower()}:{symbol.lower()}"
    if lookup in TOKEN_SYMBOL_ID:
        return TOKEN_SYMBOL_ID[lookup]
    else:
        return None


def get_prices():
    """
    Get prices for tokens in TXNS_PRICE_REQ_OUTPUT and save to PRICE_REQ_OUTPUT.
    """

    # Read in txns from TXNS_PRICE_REQ_OUTPUT
    price_reqs = []
    with open(TXNS_PRICE_REQ_OUTPUT, "r") as csvfile:
        next(csvfile)
        reader = csv.reader(csvfile)
        for row in reader:
            price_reqs.append(row)

    # Iterate through txns and get price for each
    for req in price_reqs:
        date = req[0]
        chain = req[1]
        symbol = req[2]
        token_id = req[3]

        # Deal with items to just plain skip
        if symbol.lower() in [
            'bchsv'
        ]:
            continue

        # Deal with items that need Coingecko first
        if symbol.lower() in [
            'ada',
            'algo',
            'bch',
            'bnb',
            'bsv',
            'btc',
            'xlm',
        ]:
            date_obj = datetime.strptime(date, "%Y-%m-%d %H:%M:%S")
            price = cg.get_historical_price(symbol, date_obj)
            with open(PRICE_REQ_OUTPUT, "a", newline="") as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow([date, chain, symbol, token_id, price, "coingecko"])
            continue
        
        # Fix differences in chain names for defillama API
        dl_chain = 'ethereum'
        if chain == 'ftm':
            dl_chain = 'fantom'
        elif chain == 'arb':
            dl_chain = 'arbitrum'
        elif chain == 'avax':
            dl_chain = 'avax'

        # Fix missing token ids
        if token_id is None or token_id == '' or \
            token_id in ['eth', 'ftm', 'avax', 'arb']:
            token_id = lookup_token_id(dl_chain, symbol)
            if token_id == None:
                print(f"WARN: No token id found for {chain.lower()}:{symbol.lower()}")
                continue

        price = dl.get_price(date, dl_chain, symbol, token_id)
        with open(PRICE_REQ_OUTPUT, "a", newline="") as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow([date, chain, symbol, token_id, price, "defillama"])


def main():
    reset_prices_file()
    get_prices()
    # merge_prices_with_txns()

if __name__ == "__main__":
    main()