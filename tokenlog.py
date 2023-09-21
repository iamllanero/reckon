import pandas as pd
import numpy as np
import sys


def main(token: str) -> None:
    # Read the CSV
    df = pd.read_csv('data/priced.csv')

    # Filter by the token
    df = df[df['symbol'].str.lower() == token.lower()].copy()
    df = df[df['txn_type'].isin(['buy', 'sell', 'income'])]

    df.loc[df['txn_type'] == 'income', 'usd_value'] = 0

    # Create a multiplier column
    df['multiplier'] = np.where(df['txn_type'].isin(['buy', 'income']), 1, 
                                np.where(df['txn_type'].isin(['sell']), -1, 0))

    df['unit'] = df['usd_value'] / df['qty']

    # Compute cumulative total
    df['adjusted_qty'] = df['qty'] * df['multiplier']
    df['cumul_qty'] = df['adjusted_qty'].cumsum()

    # Compute cumulative usd total
    df['adjusted_usd_value'] = df['usd_value'] * df['multiplier']
    df['cumul_usd_value'] = df['adjusted_usd_value'].cumsum()

    df['cumul_unit'] = df['cumul_usd_value'] / df['cumul_qty']

    pd.set_option('display.max_rows', None)  # Display unlimited rows
    pd.set_option('display.float_format', '{:.2f}'.format)
    print(f"Buy/Sell/Income Log for {token}")
    print(df[[
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
    
    others = 


if __name__ == '__main__':

    if len(sys.argv) > 1:
        token = sys.argv[1]
        main(token)
    else:
        print("Usage: python3 tokenlog.py <token>")
