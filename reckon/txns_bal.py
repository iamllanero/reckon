import pandas as pd
import sys
from config import TXNS_OUTPUT

def main(token: str) -> None:
    # Read the CSV
    df = pd.read_csv(TXNS_OUTPUT)

    # Filter by the token
    df = df[df['symbol'].str.lower() == token.lower()].copy()
    txn_df = df[df['txn_type'].isin(['buy', 'sell', 'income', 'receive'])]

    # Create a multiplier column
    condition = txn_df['txn_type'].isin(['buy', 'income', 'receive'])
    txn_df.loc[condition, 'multiplier'] = 1

    condition = txn_df['txn_type'].isin(['sell'])
    txn_df.loc[condition, 'multiplier'] = -1

    # Compute cumulative total
    txn_df['adjusted_qty'] = txn_df['qty'] * txn_df['multiplier']
    txn_df['cumul_qty'] = txn_df['adjusted_qty'].cumsum()

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
        'cumul_qty',
        'chain',
        'project',
        'token_id',
        ]].to_string(index=False, header=True))

    other_df = df[~df['txn_type'].isin(['buy', 'sell', 'income', 'receive'])]

    if len(other_df) > 0:    
        print(f"Other Txns Log for {token}")
        print(other_df[[
            'date', 
            'txn_type', 
            'qty', 
            'symbol', 
            'purchase_token_cost',
            'purchase_token',
            'chain',
            'project',
            'token_id',
            ]].to_string(index=False, header=True))


if __name__ == '__main__':

    if len(sys.argv) > 1:
        token = sys.argv[1]
        main(token)
    else:
        print("Usage: python3 tokenlog.py <token>")
