import csv
import defillama as dl
import coingecko as cg
from datetime import datetime
from config import (
    TXNS_PRICE_REQ_OUTPUT, 
    TXNS_OUTPUT,
    PRICE_REQ_OUTPUT, 
    PRICE_INFERRED_OUTPUT,
    PRICE_MERGED_OUTPUT,
    PRICE_MISSING_OUTPUT,
    PRICEV2_OUTPUT,
    STABLECOINS,
)

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

    with open(PRICE_INFERRED_OUTPUT, "w", newline="") as csvfile:
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
        (
            date,
            chain,
            qty,
            symbol,
            token_id,
            txn_type,
            purchase_token_cost,
            purchase_token,
            purchase_token_id,
        ) = req

        # Ignore certain tokens
        if symbol.lower() in [
            'bchsv'
        ]:
            continue

        # Let's try to get the price!
        price = None
        source = None

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
            source = "coingecko"
            # with open(PRICE_REQ_OUTPUT, "a", newline="") as csvfile:
            #     writer = csv.writer(csvfile)
            #     writer.writerow([date, chain, symbol, token_id, price, "coingecko"])
            # continue
        
        # Deal with other items using DefiLlama
        else:
            # Get chain names for defillama API
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

            if price != None and price != '':
                source = "defillama"
            else:
                source = "not found"

        # Save price to file
        with open(PRICE_REQ_OUTPUT, "a", newline="") as csvfile:

            writer = csv.writer(csvfile)
            writer.writerow([
                date, 
                chain, 
                symbol, 
                token_id, 
                price, 
                source
            ])

        # Infer prices if data is available and qquanitities are significant
        if price != None and \
            not purchase_token.lower() in STABLECOINS and \
            purchase_token != None and \
            purchase_token != '' and \
            purchase_token_cost != None and \
            purchase_token_cost != '' and \
            float(qty) > 0.1 and \
            float(purchase_token_cost) > 0.1:

            inferred_price = float(qty) * float(price) / float(purchase_token_cost)
            with open(PRICE_INFERRED_OUTPUT, "a", newline="") as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow([
                    date, 
                    chain, 
                    purchase_token, 
                    purchase_token_id, 
                    inferred_price, 
                    "inferred"
                ])
                

# TODO SHould optimize this to be a global variable rather than reading the
# file each time.
def get_price(date, chain, symbol, token_id):
    """
    Get price for a single token using the PRICE_REQ_OUTPUT file.

    Note that assumes get_prices() has been run which creates the file based
    on DefiLlama or Coingecko data.
    """
    with open(PRICE_MERGED_OUTPUT, "r") as csvfile:
        next(csvfile)
        reader = csv.reader(csvfile)
        for row in reader:
            if row[0] == date and row[1] == chain and row[2] == symbol and row[3] == token_id:
                return row[4]
    return None


def merge_inferred_prices():
    """
    Merge inferred prices into requested prices.
    
    Favor prices that were requested over inferred prices.
    """

    print("Merging requested and inferred prices...")

    price_reqs = []
    inferred_prices = []
    merged_prices = []
    missing_prices = []

    total_count = 0
    inferred_count = 0
    missing_count = 0
    
    with open(PRICE_REQ_OUTPUT, "r") as csvfile:
        next(csvfile)
        reader = csv.reader(csvfile)
        for row in reader:
            price_reqs.append(row)
    
    with open(PRICE_INFERRED_OUTPUT, "r") as csvfile:
        next(csvfile)
        reader = csv.reader(csvfile)
        for row in reader:
            inferred_prices.append(row)

    for req in price_reqs:
        (date,
         chain,
         symbol,
         token_id,
         price,
         source
         ) = req
        total_count += 1
        if source == 'not found':
            for row in inferred_prices:
                (inferred_date,
                 inferred_chain,
                 inferred_symbol,
                 inferred_token_id,
                 inferred_price,
                 inferred_source
                 ) = row
                if inferred_date == date and \
                    inferred_chain.lower() == chain.lower() and \
                    inferred_symbol.lower() == symbol.lower() and \
                    inferred_token_id.lower() == token_id.lower():

                    inferred_count += 1
                    merged_prices.append([
                        date,
                        chain,
                        symbol,
                        token_id,
                        inferred_price,
                        inferred_source,
                    ])
                    break

            missing_count += 1
            missing_prices.append([
                date,
                chain,
                symbol,
                token_id,
                price,
                "missing",
            ])

        else:
            merged_prices.append([
                date,
                chain,
                symbol,
                token_id,
                price,
                source,
            ])

    with open(PRICE_MERGED_OUTPUT, "w", newline="") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["date", "chain", "symbol", "token_id", "price", "source"])
        writer.writerows(merged_prices)
    
    with open(PRICE_MISSING_OUTPUT, "w", newline="") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["date", "chain", "symbol", "token_id", "price", "source"])
        writer.writerows(missing_prices)

    print(f"- Total: {total_count}")
    print(f"- Inferred: {inferred_count}")
    print(f"- Missing: {missing_count}")


def create_priced_txns():
    """
    Create PRICEV2_OUTPUT based on buy, sell, income txns with pricing data.
    """

    print("Creating priced txns file...")
    with open(TXNS_OUTPUT, "r", newline="") as csvfile:
        count_total = 0
        count_ignored = 0
        count_stablecoin = 0
        count_dlcg = 0
        count_missing = 0

        price_txns = []
        headers = next(csvfile).strip().split(",")
        reader = csv.reader(csvfile)
        for row in reader:
            count_total += 1
            date = row[headers.index("date")]
            txn_type = row[headers.index("txn_type")]
            qty = row[headers.index("qty")]
            symbol = row[headers.index("symbol")]
            token_id = row[headers.index("token_id")]
            purchase_token_cost = row[headers.index("purchase_token_cost")]
            purchase_token = row[headers.index("purchase_token")]
            purchase_token_id = row[headers.index("purchase_token_id")]
            chain = row[headers.index("chain")]
            project = row[headers.index("project")]
            txn_name = row[headers.index("txn_name")]
            wallet = row[headers.index("wallet")]
            id = row[headers.index("id")]

            # Skip non-buy, sell, income txns
            if txn_type.lower() not in ['buy', 'sell', 'income']:
                count_ignored += 1
                continue

            # Handle stablecoins
            if purchase_token.lower() in STABLECOINS:
                usd_value = purchase_token_cost
                price_txns.append([
                    date, 
                    txn_type, 
                    qty, 
                    symbol, 
                    token_id, 
                    usd_value,
                    purchase_token_cost, 
                    purchase_token, 
                    purchase_token_id, 
                    chain, 
                    project, 
                    txn_name, 
                    wallet, 
                    id, 
                    'stablecoin',
                ])
                count_stablecoin += 1
                continue

            price = get_price(date, chain, symbol, token_id)

            if price != None and price != '':
                if qty != None and qty != '':
                    usd_value = float(qty) * float(price)
                else:
                    print(f"WARN: Missing qty {date} {chain} {symbol} {token_id}")
                    usd_value = '0.00'
                price_txns.append([
                    date, 
                    txn_type, 
                    qty, 
                    symbol, 
                    token_id, 
                    usd_value,
                    purchase_token_cost, 
                    purchase_token, 
                    purchase_token_id, 
                    chain, 
                    project, 
                    txn_name, 
                    wallet, 
                    id, 
                    'dlcg',
                ])
                count_dlcg += 1
            else:
                price_txns.append([
                    date, 
                    txn_type, 
                    qty, 
                    symbol, 
                    token_id, 
                    'MISSING',
                    purchase_token_cost, 
                    purchase_token, 
                    purchase_token_id, 
                    chain, 
                    project, 
                    txn_name, 
                    wallet, 
                    id, 
                    'MISSING',
                ])
                count_missing += 1

        print(f"- Total txns: {count_total}")
        print(f"- Ignored txns: {count_ignored}")
        print(f"- Stablecoin txns: {count_stablecoin}")
        print(f"- DLCG txns: {count_dlcg}")
        print(f"- Missing txns: {count_missing}")

        with open(PRICEV2_OUTPUT, "w", newline="") as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow([
                "date", 
                "txn_type", 
                "qty", 
                "symbol", 
                "token_id", 
                "usd_value",
                "purchase_token_cost", 
                "purchase_token", 
                "purchase_token_id", 
                "chain", 
                "project", 
                "txn_name", 
                "wallet", 
                "id", 
                "source",
            ])
            writer.writerows(price_txns)


def main():

    reset_prices_file()
    get_prices()
    merge_inferred_prices()
    create_priced_txns()

if __name__ == "__main__":
    main()