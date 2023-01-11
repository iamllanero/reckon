import pandas as pd
from reckon.utils import list_to_csv

def main():
    """
    Generate a csv with the following columns:
    - Symbol
    - Date acquired
    - Date sold
    - Proceeds
    - Cost basis
    - Gain or loss
    """

    df = pd.read_csv('data/priced.csv')

    df = df.astype({
        'date': 'datetime64[ns]',
        'txn_type': 'string',
        'qty': 'float64',
        'symbol': 'string',
        'purchase_token_cost': 'float64',
        'purchase_token': 'string',
        'usd_cost': 'float64',
        'txn_name': 'string',
        'chain': 'string',
        'project': 'string',
        'wallet': 'string',
        'url': 'string',
        'id': 'string',
        'usd_value': 'float64',
    })

    symbol = 'ETH'
    df = df.query("symbol == @symbol and txn_type \
        in ['buy', 'sell', 'income']")\
            .sort_values(by=['date'])\
                .copy()\
                    .reset_index(drop=True)
    df['qty_unsold'] = df['qty']
    df['unit_value'] = df['usd_value'] / df['qty']
    sell_list = [[
        'symbol',
        'qty',
        'date sold',
        'date acquired',
        'proceeds',
        'cost basis',
        'gain loss',
        'proceeds unit',
        'cost unit',
        ]]
    for i, row in df.iterrows():
        if row['txn_type'] == 'sell':
            qty_to_sell = row['qty']
            while qty_to_sell > 0:
                hi_row = df[
                    ((df['txn_type'] == 'buy') | (df['txn_type'] == 'income')) \
                        & (df['qty_unsold'] > 0)]['unit_value']\
                            .iloc[0:i].idxmax()
                hi_unsold = df.iloc[hi_row]['qty_unsold']
                cost_basis = 0
                proceeds = 0
                qty_sold = 0
                if qty_to_sell <= hi_unsold:
                    # Sold everything against one buy
                    qty_sold = qty_to_sell
                    df.iloc[hi_row, df.columns.get_loc('qty_unsold')] -= qty_to_sell
                    qty_to_sell = 0
                    cost_basis = df.iloc[hi_row]['usd_value']
                    proceeds = row['usd_value']
                else:
                    # Sold only partial against a buy; need to keep going
                    qty_sold = df.iloc[hi_row]['qty_unsold']
                    qty_to_sell -= df.iloc[hi_row]['qty_unsold']
                    df.iloc[hi_row, df.columns.get_loc('qty_unsold')] = 0
                    cost_basis = hi_unsold * df.iloc[hi_row]['unit_value']
                    proceeds = hi_unsold * row['unit_value']
                sell_list.append([
                    symbol,
                    qty_sold,
                    row['date'],
                    df.iloc[hi_row]['date'],
                    proceeds,
                    cost_basis,
                    proceeds - cost_basis,
                    row['unit_value'],
                    df.iloc[hi_row]['unit_value'],
                ])

    list_to_csv(sell_list, 'data/8949-hifo.csv')

if __name__ == '__main__':
    main()