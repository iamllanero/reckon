import pandas as pd
from reckon.utils import list_to_csv

def main():
    """
    Quick implementation of a rudimentary portfolio view.
    """

    df = pd.read_csv('data/priced.csv')
    df = df.astype({
            'date': 'datetime64[ns]',
            'txn_type': 'string',
            'qty': 'float64',
            'symbol': 'string',
            'purchase_token_cost': 'float64',
            'purchase_token': 'string',
            'txn_name': 'string',
            'chain': 'string',
            'project': 'string',
            'wallet': 'string',
            'url': 'string',
            'id': 'string',
            'usd_value': 'float64',
        })

    pf = [[
        'symbol',
        'current_qty',
        'gain_loss_usd',
        'unit_cost',
        'buy_qty',
        'buy_usd',
        'buy_unit',
        'sell_qty',
        'sell_usd',
        'sell_unit',
        'income_qty',
        'income_usd',
    ]]

    for symbol, sf in df.groupby('symbol'):
        buy_qty = sf[(sf['txn_type'] == 'buy')]['qty'].sum()
        buy_usd = sf[(sf['txn_type'] == 'buy')]['usd_value'].sum()
        sell_qty = sf[(sf['txn_type'] == 'sell')]['qty'].sum()
        sell_usd = sf[(sf['txn_type'] == 'sell')]['usd_value'].sum()
        income_qty = sf[(sf['txn_type'] == 'income')]['qty'].sum()
        income_usd = sf[(sf['txn_type'] == 'income')]['usd_value'].sum()
        # buy_unit = ''
        # sell_unit = ''
        # gain_loss_usd = ''
        # current_qty = ''
        buy_unit = buy_usd / buy_qty if buy_qty > 0 else ''
        sell_unit = sell_usd / sell_qty if sell_qty > 0 else ''
        gain_loss_usd = buy_usd + income_usd - sell_usd
        current_qty = buy_qty + income_qty - sell_qty
        unit_cost = (buy_usd - sell_usd) / current_qty if current_qty > 0 else ''
        pf.append([
            symbol,
            current_qty,
            gain_loss_usd,
            unit_cost,
            buy_qty,
            buy_usd,
            buy_unit,
            sell_qty,
            sell_usd,
            sell_unit,
            income_qty,
            income_usd,
        ])

    list_to_csv(pf, 'data/pf.csv')


if __name__ == '__main__':
    main()
