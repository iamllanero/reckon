import csv
import defillama as dl
import coingecko as cg
import sys
import tomllib
from datetime import datetime
from config import (
    PRICE_CONFIG,
    PRICE_INFERRED_OUTPUT,
    PRICE_MANUAL_FILE,
    PRICE_MERGED_OUTPUT,
    PRICE_MISSING_OUTPUT,
    PRICE_REQ_OUTPUT,
    PRICE_OUTPUT,
    PRICE_WORKSHEET_OUTPUT,
    STABLECOINS,
    TXNS_OUTPUT,
    TXNS_PRICE_REQ_OUTPUT,
)


class PriceRule:


    def __init__(self, entry):

        self.chain = entry['chain'] if 'chain' in entry else '*'
        self.symbol = entry['symbol'] if 'symbol' in entry else '*'
        self.token_id = entry['token_id'] if 'token_id' in entry else '*'
        self.action = entry['action'] if 'action' in entry else 'defillama'
        self.params = {k: v for k, v in entry.items() if k not in [
            "symbol",
            "action",
            "chain",
            "token_id"
        ]}


    def __repr__(self):
        return f"{self.__class__.__name__}({self.chain}, {self.symbol}, {self.token_id}, {self.action}, {self.params})"


    def _matches_pattern(self, pattern, value):
        if pattern is None or pattern == "*":
            return True
        return pattern.lower() == value.lower()


    def match(self, chain, symbol, token_id):
        return (self._matches_pattern(self.chain, chain) and
                self._matches_pattern(self.symbol, symbol) and
                self._matches_pattern(self.token_id, token_id))


    def get_info(self, chain, symbol, token_id):

        # Look up any params and use them
        if 'map_chain_to' in self.params:
            chain = self.params['map_chain_to']
        if 'map_symbol_to' in self.params:
            symbol = self.params['map_symbol_to']
        if 'map_token_id_to' in self.params:
            token_id = self.params['map_token_id_to'] 
        return (chain, symbol, token_id)


    def get_price(self, date, chain, symbol, token_id):
        print(f"WARN: Using default price rule for {date} {chain} {symbol} {token_id}")
        return (chain, symbol, token_id, None, None)


    def ignore(self):
        return self.action == "ignore"


class CoinGeckoPriceRule(PriceRule):


    def get_price(self, date, chain, symbol, token_id):
        source = "coingecko"
        date_obj = datetime.strptime(date, "%Y-%m-%d %H:%M:%S")
        price = cg.get_historical_price(symbol, date_obj)
        if price == None or price == '':
            source += " / price not found"
        return (chain, symbol, token_id, price, source)


class DefiLlamaPriceRule(PriceRule):

    def get_price(self, date, chain, symbol, token_id):
        source = "defillama"

        # Look up any params and use them
        if 'map_chain_to' in self.params:
            chain = self.params['map_chain_to']
        if 'map_symbol_to' in self.params:
            symbol = self.params['map_symbol_to']
        if 'map_token_id_to' in self.params:
            token_id = self.params['map_token_id_to'] 

        # Map chain names to defillama API
        dl_chain = None
        if chain.lower() == 'eth':
            dl_chain = 'ethereum'
        elif chain.lower() == 'ftm':
            dl_chain = 'fantom'
        elif chain.lower() == 'arb':
            dl_chain = 'arbitrum'
        elif chain.lower() == 'avax':
            dl_chain = 'avax'
        else:
            print(
                f"WARN: No chain mapping for {date} {chain} {symbol} {token_id}")
            source += " / no chain mapping"

        # Fix missing token ids
        if token_id == None:
            print(
                f"WARN: No token id found for {chain.lower()}:{symbol.lower()}")
            source += " / no token_id"

        # Get the price
        price = dl.get_price(date, dl_chain, symbol, token_id)
        if price == None or price == '':
            source += " / price not found"

        return (chain, symbol, token_id, price, source)


class PriceRulesConfig:

    def __init__(self):
        print('Loading price rules config...')
        # Read in the price config rules
        self.rules = []
        with open(PRICE_CONFIG, "rb") as f:
            rules_toml = tomllib.load(f)["rules"]
            for entry in rules_toml:
                action = entry['action'] if 'action' in entry else 'defillama'

                if action == 'defillama':
                    rule = DefiLlamaPriceRule(entry)
                elif action == 'coingecko':
                    rule = CoinGeckoPriceRule(entry)
                elif action == 'ignore':
                    rule = PriceRule(entry)
                else:
                    print(f"WARN: Unknown action {action} in price config")
                    sys.exit(1)
                print(f"- {rule}")
                self.rules.append(rule)


    def find_rule(self, chain, symbol, token_id):
        for rule in self.rules:
            if rule.match(chain, symbol, token_id):
                return rule
        return None


def reset_prices_file():
    """
    Reset the prices file to just the header.
    """

    print("Resetting prices file...")

    with open(PRICE_REQ_OUTPUT, "w", newline="") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["date", "chain", "symbol",
                        "token_id", "price", "source"])

    with open(PRICE_INFERRED_OUTPUT, "w", newline="") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["date", "chain", "symbol",
                        "token_id", "price", "source"])


def get_prices():
    """
    Get prices for tokens in TXNS_PRICE_REQ_OUTPUT and save to PRICE_REQ_OUTPUT.
    """

    print("Getting prices...")

    price_rules_config = PriceRulesConfig()

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

        # Let's try to get the price!
        price = None
        source = None

        # Get the action for this token request based on the price rules config
        rule = price_rules_config.find_rule(chain, symbol, token_id)
        # print(f"- Match {date} {symbol} {token_id} => {rule}")

        if rule.action == "ignore":
            print(f"- INFO: Ignoring {date} {chain} {symbol} {token_id}")
            continue

        (chain, symbol, token_id, price, source) = rule.get_price(date, chain, symbol, token_id)

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

            inferred_price = float(qty) * float(price) / \
                float(purchase_token_cost)
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

    # The txns_price_req.csv file with pricing information (incl. missing)
    price_reqs = []
    # The inferred prices from every txn that was missing a price
    inferred_prices = []
    # The merged prices with inferred prices replacing missing prices
    merged_prices = []
    # The missing prices that were not gotten from an api, inferred, or manual
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
        if "not found" in source:
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
        writer.writerow(["date", "chain", "symbol",
                        "token_id", "price", "source"])
        writer.writerows(merged_prices)

    with open(PRICE_MISSING_OUTPUT, "w", newline="") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["date", "chain", "symbol",
                        "token_id", "price", "source"])
        writer.writerows(missing_prices)

    print(f"- Total: {total_count}")
    print(f"- Inferred: {inferred_count}")
    print(f"- Missing: {missing_count}")


def create_priced_txns():
    """
    Create PRICE_OUTPUT based on buy, sell, income txns with pricing data.
    """

    print("Creating priced txns file...")

    price_rules_config = PriceRulesConfig()

    # Read in manual prices
    manual_prices = []
    with open(PRICE_MANUAL_FILE, "r") as csvfile:
        next(csvfile)
        reader = csv.reader(csvfile)
        for row in reader:
            # Check if the row (line) starts with a hash (#)
            if row[0].strip().startswith("#"):
                continue
            manual_prices.append(row)


    with open(TXNS_OUTPUT, "r", newline="") as csvfile:
        count_total = 0
        count_manual = 0
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

            # Get the action for this token request based on the price rules config
            rule = price_rules_config.find_rule(chain, symbol, token_id)
            # Remap the chain, symbol, token_id if needed
            (chain, symbol, token_id) = rule.get_info(chain, symbol, token_id)

            # Handle manual prices
            continue_outer_loop = False
            for manual_price in manual_prices:
                (
                    manual_date,
                    manual_symbol,
                    manual_chain,
                    manual_token_id,
                    manual_timestamp,
                    manual_price,
                    manual_txn_type,
                    manual_comment,
                ) = manual_price
                if manual_date == date and \
                        manual_symbol.lower() == symbol.lower() and \
                        manual_chain.lower() == chain.lower() and \
                        manual_token_id.lower() == token_id.lower():
                    print(f"- INFO: Using manual price for {date} {chain} {symbol} {token_id}")
                    if manual_txn_type != None and manual_txn_type != '':
                        print(f"-- INFO: Using manual txn type {manual_txn_type} for {id}")
                        txn_type = manual_txn_type
                    price_txns.append([
                        date,
                        txn_type,
                        qty,
                        symbol,
                        token_id,
                        float(manual_price) * float(qty),
                        purchase_token_cost,
                        purchase_token,
                        purchase_token_id,
                        chain,
                        project,
                        txn_name,
                        wallet,
                        id,
                        f'manual / {manual_comment}',
                    ])
                    count_manual += 1
                    continue_outer_loop = True
                    break
            if continue_outer_loop:
                continue

            # Skip non-buy, sell, income txns
            if txn_type.lower() not in ['buy', 'sell', 'income']:
                count_ignored += 1
                continue

            # Handle purchased in stablecoins
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
                    'stablecoin/purchase',
                ])
                count_stablecoin += 1
                continue

            # Handle sold or income in stablecoins
            if symbol.lower() in STABLECOINS:
                usd_value = qty
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
                    'stablecoin/sellincome',
                ])
                count_stablecoin += 1
                continue

            price = get_price(date, chain, symbol, token_id)

            if price != None and price != '':
                if qty != None and qty != '':
                    usd_value = float(qty) * float(price)
                else:
                    print(
                        f"WARN: Missing qty {date} {chain} {symbol} {token_id}")
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
        print(f"- Manual txns: {count_manual}")
        print(f"- Ignored txns: {count_ignored}")
        print(f"- Stablecoin txns: {count_stablecoin}")
        print(f"- DLCG txns: {count_dlcg}")
        print(f"- Missing txns: {count_missing}")

        with open(PRICE_OUTPUT, "w", newline="") as csvfile:
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


def create_worksheet():
    """
    Create worksheet for manual price entry.
    """

    with open(PRICE_OUTPUT, newline="", mode="r") as csvfile:
        reader = csv.reader(csvfile)
        headers = next(reader)
        missing = [row for row in reader if row[int(headers.index("source"))] == "MISSING"]

    with open(PRICE_WORKSHEET_OUTPUT, newline="", mode="w") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow([
            'date',
            'symbol',
            'chain',
            'token_id',
            'timestamp',
            'price',
            'txn_type',
            'comment',
        ])
        for row in missing:
            writer.writerow([
                row[int(headers.index("date"))],
                row[int(headers.index("symbol"))],
                row[int(headers.index("chain"))],
                row[int(headers.index("token_id"))],
                dl.get_timestamp_from_date(row[int(headers.index("date"))]),
                '',
                '',
                '',
            ])


def main():

    reset_prices_file()
    get_prices()
    merge_inferred_prices()
    create_priced_txns()
    create_worksheet()


if __name__ == "__main__":
    main()
