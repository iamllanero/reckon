import pandas as pd
import coingecko as cg
from config import TXNS_OUTPUT, PRICE_OUTPUT, STABLECOINS

def compute_value(
    date, 
    txn_type,
    qty, 
    name, 
    purchase_token_cost, 
    purchase_token, 
    ):

    if txn_type not in ['buy', 'sell', 'income']:
        return

    # if not math.isnan(usd_cost):
    #     return usd_cost

    if type(purchase_token) is str and \
        purchase_token.lower() in STABLECOINS:
        # print(f'WARN: Pricing a stablecoin for {qty} {name} <= {purchase_token_cost} {purchase_token}')
        return purchase_token_cost

    if type(name) is str and \
        name.lower() in STABLECOINS:
        # print(f'WARN: Pricing a stablecoin for {qty} {name} <= {purchase_token_cost} {purchase_token}')
        return qty

    price = cg.get_historical_price(name, date.to_pydatetime())

    if price != None:
        value = price * qty
        if type(purchase_token) is str and purchase_token != '':
            purchase_token_price = value / purchase_token_cost
            cg.save_historical_price(purchase_token, date.to_pydatetime(), purchase_token_price, "Inferred")
        return value



def main():
    """
    From txns.csv
    date,txn_type,qty,symbol,purchase_token_cost,purchase_token,usd_cost,txn_name,chain,project,wallet,url,id
    """
    df = pd.read_csv(TXNS_OUTPUT)

    df = df.astype({
        'date': 'datetime64[ns]',
        'txn_type': 'category',
        'qty': 'float64',
        'symbol': 'category',
        'purchase_token_cost': 'float64',
        'purchase_token': 'category',
        'txn_name': 'category',
        'chain': 'category',
        'project': 'category',
        'wallet': 'category',
        'id': 'string',
        'url': 'string',
    })

    df['usd_value'] = df.apply(
        lambda x: (compute_value(
            x['date'], 
            x['txn_type'],
            x['qty'], 
            x['symbol'], 
            x['purchase_token_cost'],
            x['purchase_token'],
        )),
        axis=1)

    df[[
        'date',
        'txn_type',
        'qty',
        'symbol',
        'purchase_token_cost',
        'purchase_token',
        'usd_value',
        'txn_name',
        'chain',
        'project',
        'wallet',
        'id',
        'url',
    ]].to_csv(PRICE_OUTPUT, index=False)

    # TODO Should create an output file of unpriced transactions.
    #      Especially if it can be used directly to fill price_cache.csv

    cg.clean_caches()


if __name__ == '__main__':
    main()
