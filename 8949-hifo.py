import pandas as pd
from utils import list_to_csv

def main():
    """
    Generate a csv with the following columns:
    - Symbol
    - Date acquired
    - Date sold
    - Proceeds
    - Cost basis
    - Gain or loss
    - Uses the HIFO (highest
    """

    df = pd.read_csv('data/priced.csv')

    df = df.astype({
        'date': 'datetime64[ns]',
        'txn_type': 'string',
        'qty': 'float64',
        'symbol': 'string',
        'purchase_token_cost': 'float64',
        'purchase_token': 'string',
        'unit_cost': 'float64',
        'usd_cost': 'float64',
        'txn_name': 'string',
        'chain': 'string',
        'project': 'string',
        'wallet': 'string',
        'source': 'string',
        'usd_value': 'float64',
    })

    df['unit_value'] = df['usd_value'] / df['qty']
    df['qty_unsold'] = df['qty']

    df.reindex()

    sell_list = [['Symbol', 
        'Date of Sale', 
        'Date of Buy', 
        'Qty Sold', 
        'Proceeds', 
        'Cost Basis', 
        'Gain Loss']]

    for index, row in df[(df['symbol'] == 'ETH') & \
                        (df['txn_type'] == 'sell')].iterrows():
        qty_to_sell = row['qty']
        print(f"{index}: sold {qty_to_sell} on {row['date']} for {row['usd_value']}")
        cost_basis = 0
        while qty_to_sell > 0:
            sell_row = ['ETH', row['date']]
            # hi_row = eth_buy['unit_value'].iloc[0:index].idxmax()
            hi_row = df[(df['symbol'] == 'ETH') & \
                ((df['txn_type'] == 'buy') | (df['txn_type'] == 'income')) & \
                (df['qty_unsold'] > 0)]['unit_value'].iloc[0:index].idxmax()
            if qty_to_sell <= df.iloc[hi_row]['qty_unsold']:
                df.iloc[hi_row, df.columns.get_loc('qty_unsold')] -= qty_to_sell
                qty_to_sell = 0
            else:
                qty_to_sell -= df.iloc[hi_row]['qty_unsold']
                df.iloc[hi_row, df.columns.get_loc('qty_unsold')] = 0
            print(f"- {hi_row}: match {df.iloc[hi_row]['txn_type']} on {df.iloc[hi_row]['date']} for {df.iloc[hi_row]['qty']} | remaining: {df.iloc[hi_row]['qty_unsold']}")
            cost_basis += float(df.iloc[hi_row]['usd_value'])
            proceeds = float(df.iloc[hi_row]['qty']) / \
                float(df.iloc[index]['qty']) * \
                float(df.iloc[index]['usd_value'])
            sell_row.extend([df.iloc[hi_row]['date'],
                df.iloc[hi_row]['qty'],
                proceeds,
                cost_basis,
                proceeds - cost_basis
                ])
            sell_list.append(sell_row)
        print(f"  - cost basis: {cost_basis}")
        print(f"  - gain/loss: {row['usd_value'] - cost_basis}")

    list_to_csv(sell_list, 'data/8949-hifo.csv')


if __name__ == '__main__':
    main()