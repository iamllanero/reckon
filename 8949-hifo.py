import pandas as pd

def main():

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
    for index, row in df[(df['symbol'] == 'ETH') & \
                        (df['txn_type'] == 'sell')].iterrows():
        qty_to_sell = row['qty']
        print(f"{index}: sold {qty_to_sell} on {row['date']} for {row['usd_value']}")
        cost_basis = 0
        while qty_to_sell > 0:
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
            cost_basis += df.iloc[hi_row]['usd_value']
        print(f"  - cost basis: {cost_basis}")
        print(f"  - gain/loss: {row['usd_value'] - cost_basis}")


if __name__ == '__main__':
    main()