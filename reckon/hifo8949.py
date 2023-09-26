import pandas as pd
from utils import list_to_csv
from config import HIFO8949_OUTPUT, PRICE_OUTPUT

def calc_sell(df, symbol):
    """
    Calculates for every sale, the matching buy/income lot(s).

    Returns:
        List - Each item is a list representing a sell/buy lot
    """

    if symbol == None:
        return

    # Get a clean dataframe (scope down to single token and taxable tx types)
    df = df.query("symbol == @symbol and txn_type in ['buy', 'sell', 'income']")\
        .copy()\
        .sort_values(by=['date'])\
        .reset_index(drop=True)

    # Augment with additional columns
    df['qty_unsold'] = df['qty'].where(df['txn_type'] != 'sell')
    df['unit_value'] = df['usd_value'] / df['qty']

    # Create list for tracking the tokens sold
    sell_list = []

    # Start looking through the transaction dataframe
    for i, row in df.iterrows():
        if row['txn_type'] == 'sell':
            qty_to_sell = row['qty']
            unit_price_sold = row['unit_value']
            while qty_to_sell > 0:
                # Check that there are any buys
                if len(df.iloc[0:i].query("txn_type in ['buy', 'income'] and qty_unsold > 0")) == 0:
                    print(f"WARN: No buy/income found for {row['qty']} {row['symbol']} sold on {row['date']}")
                    return sell_list
                # Find the highest cost basis in transactions prior to current
                hi_row = (df.iloc[0:i].query("txn_type in ['buy', 'income'] and qty_unsold > 0")
                    )['unit_value'].idxmax()
                hi_unsold = df.iloc[hi_row]['qty_unsold']
                unit_price_cost = df.iloc[hi_row]['unit_value']
                # cost_basis = 0
                # proceeds = 0
                qty_sold = 0
                if qty_to_sell <= hi_unsold:
                    # Sold everything against one buy
                    qty_sold = qty_to_sell
                    df.iloc[hi_row, df.columns.get_loc('qty_unsold')] -= qty_to_sell
                    qty_to_sell = 0
                    # cost_basis = df.iloc[hi_row]['usd_value']
                    # proceeds = row['usd_value']
                else:
                    # Sold only partial against a buy; need to keep going
                    qty_sold = df.iloc[hi_row]['qty_unsold']
                    qty_to_sell -= df.iloc[hi_row]['qty_unsold']
                    df.iloc[hi_row, df.columns.get_loc('qty_unsold')] = 0
                cost_basis = qty_sold * unit_price_cost
                proceeds = qty_sold * unit_price_sold
                sell_list.append([
                    symbol,
                    qty_sold,
                    row['date'],
                    row['date'].year,
                    df.iloc[hi_row]['date'],
                    proceeds,
                    cost_basis,
                    proceeds - cost_basis,
                    unit_price_sold,
                    unit_price_cost,
                ])

    return sell_list

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

    df = pd.read_csv(PRICE_OUTPUT)

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

    # Create list for tracking the tokens sold
    sell_list = [[
        'symbol',
        'qty',
        'date sold',
        'year sold',
        'date acquired',
        'proceeds',
        'cost basis',
        'gain loss',
        'proceeds unit',
        'cost unit',
        ]]

    symbols = df['symbol'].unique()

    for symbol in symbols:
        print(f"INFO: Calculating symbol {symbol}")
        sell_list.extend(calc_sell(df, symbol))

    # df.to_csv('data/8949-hifo-wip.csv')
    list_to_csv(sell_list, HIFO8949_OUTPUT)

if __name__ == '__main__':
    main()