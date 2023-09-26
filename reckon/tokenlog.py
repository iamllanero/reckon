import pandas as pd
import sys
from config import PRICE_OUTPUT


def main(token: str) -> None:
    # Read the CSV
    df = pd.read_csv(PRICE_OUTPUT)

    # Filter by the token
    df = df[df['symbol'].str.lower() == token.lower()].copy()
    txn_df = df[df['txn_type'].isin(['buy', 'sell', 'income', 'receive'])]

    txn_df.loc[txn_df['txn_type'] == 'income', 'usd_value'] = 0
    txn_df.loc[txn_df['txn_type'] == 'receive', 'usd_value'] = 0

    # Create a multiplier column
    condition = txn_df['txn_type'].isin(['buy', 'income', 'receive'])
    txn_df.loc[condition, 'multiplier'] = 1

    condition = txn_df['txn_type'].isin(['sell'])
    txn_df.loc[condition, 'multiplier'] = -1

    txn_df['unit'] = txn_df['usd_value'] / txn_df['qty']

    # Compute cumulative total
    txn_df['adjusted_qty'] = txn_df['qty'] * txn_df['multiplier']
    txn_df['cumul_qty'] = txn_df['adjusted_qty'].cumsum()

    # Compute cumulative usd total
    txn_df['adjusted_usd_value'] = txn_df['usd_value'] * txn_df['multiplier']
    txn_df['cumul_usd_value'] = txn_df['adjusted_usd_value'].cumsum()

    txn_df['cumul_unit'] = txn_df['cumul_usd_value'] / txn_df['cumul_qty']

    pd.set_option('display.max_rows', None)  # Display unlimited rows
    pd.set_option('display.float_format', '{:.2f}'.format)
    print(f"Buy/Sell/Income Log for {token}")
    print(txn_df[[
        'date', 
        'txn_type', 
        'qty', 
        'symbol', 
        'purchase_token_cost',
        'purchase_token',
        'usd_value',
        'unit',
        'cumul_qty',
        'cumul_usd_value',
        'cumul_unit',
        ]].to_string(index=False, header=True))
    
    other_df = df[~df['txn_type'].isin(['buy', 'sell', 'income', 'receive'])]
    print(f"Other Txns Log for {token}")
    print(other_df[[
        'date', 
        'txn_type', 
        'qty', 
        'symbol', 
        'purchase_token_cost',
        'purchase_token',
        'usd_value',
        ]].to_string(index=False, header=True))


if __name__ == '__main__':

    if len(sys.argv) > 1:
        token = sys.argv[1]
        main(token)
    else:
        print("Usage: python3 tokenlog.py <token>")
