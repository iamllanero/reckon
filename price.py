import pandas as pd
import reckon.coingecko as cg
import math
from datetime import datetime
from reckon.constants import TXNS_FILE, PRICED_FILE, STABLECOINS

def compute_value(
    date, 
    txn_type,
    qty, 
    name, 
    purchase_token_cost, 
    purchase_token, 
    usd_cost):

    if txn_type not in ['buy', 'sell', 'income']:
        return

    if not math.isnan(usd_cost):
        return usd_cost

    if type(purchase_token) is str and \
        purchase_token.lower() in STABLECOINS:
        print(f'WARN: Pricing a stablecoin for {qty} {name} <= {purchase_token_cost} {purchase_token}')
        return purchase_token_cost

    price = cg.get_historical_price(name, date.to_pydatetime())

    if price != None:
        value = price * qty
        purchase_token_price = abs(value / qty)
        if type(purchase_token) is str and \
            purchase_token != '':
            cg.save_historical_price(purchase_token, date.to_pydatetime(), purchase_token_price, "Inferred")
        return value



def main():
    """
    From txns.csv
    date,txn_type,qty,symbol,purchase_token_cost,purchase_token,usd_cost,txn_name,chain,project,wallet,url,id
    """
    df = pd.read_csv(TXNS_FILE)

    df = df.astype({
        'date': 'datetime64[ns]',
        'txn_type': 'category',
        'qty': 'float64',
        'symbol': 'category',
        'purchase_token_cost': 'float64',
        'purchase_token': 'category',
        'usd_cost': 'float64',
        'txn_name': 'category',
        'chain': 'category',
        'project': 'category',
        'wallet': 'category',
        'url': 'string',
        'id': 'string',
    })

    df['usd_value'] = df.apply(
        lambda x: (compute_value(
            x['date'], 
            x['txn_type'],
            x['qty'], 
            x['symbol'], 
            x['purchase_token_cost'],
            x['purchase_token'],
            x['usd_cost'])),
        axis=1)

    df.to_csv(PRICED_FILE, index=False)

    # TODO Should create an output file of unpriced transactions.
    #      Especially if it can be used directly to fill price_cache.csv

    cg.clean_cache()


if __name__ == '__main__':
    main()
