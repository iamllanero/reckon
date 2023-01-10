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
        'unit_cost': 'float64',
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
    print(df)
    # df = df.query("symbol == @symbol and txn_type in ['buy', 'sell', 'income']").copy()
    # df.reindex()
    # # df = df.query("symbol == @symbol and txn_type in ['buy', 'sell', 'income']")
    # df.at[4, 'txn_type'] = 'test'
    # print(df)

    df = df[df.eval("symbol == @symbol and txn_type in ['buy', 'sell', 'income']")]
    print(df)
    


    # list_to_csv(sell_list, 'data/8949-hifo.csv')


if __name__ == '__main__':
    main()