import csv
import re
from config import STABLECOINS

# Headers from the latest coinbase reports (for 2023)

# Timestamp,
# Transaction Type,
# Asset,
# Quantity Transacted,
# Spot Price Currency,
# Spot Price at Transaction,
# Subtotal,
# Total (inclusive of fees and/or spread),
# Fees and/or Spread,
# Notes


def parse(fn):
    txns = []
    with open(fn, 'r') as f:
        # Skip first 3 lines
        next(f)
        next(f)
        next(f)
        reader = csv.reader(f)
        for row in reader:
            [
                date,
                txn_type,
                symbol,
                qty,
                cost_basis_currency,
                _,
                cost_basis,
                _,
                fee,
                notes,
            ] = row

            date = f'{date[:10]} {date[11:19]}'

            if txn_type in ['Rewards Income']:
                if float(cost_basis) > 0.40:
                    txns.append([
                        date,
                        'income',
                        qty,
                        symbol,
                        '',
                        '',
                        '',
                        '',
                        'coinbase',
                        'coinbase',
                        txn_type,
                        '',
                        fn
                    ])

            elif txn_type == 'Buy' or txn_type == 'Advance Trade Buy':

                if cost_basis_currency != 'USD':
                    print(
                        f'ERROR: Unhandled currency {cost_basis_currency} in {fn}')
                if symbol.lower() not in STABLECOINS:
                    txns.append([
                        date,
                        'buy',
                        qty,
                        symbol,
                        '',
                        cost_basis,
                        cost_basis_currency,
                        '',
                        'coinbase',
                        'coinbase',
                        txn_type,
                        '',
                        fn
                    ])

            elif txn_type == 'Sell' or txn_type == 'Advance Trade Sell':
                if cost_basis_currency != 'USD':
                    print(
                        f'ERROR: Unhandled currency {cost_basis_currency} in {fn}')
                if symbol.lower() not in STABLECOINS:
                    txns.append([
                        date,
                        'sell',
                        qty,
                        symbol,
                        '',
                        cost_basis,
                        cost_basis_currency,
                        '',
                        'coinbase',
                        'coinbase',
                        txn_type,
                        '',
                        fn
                    ])

            elif txn_type in ['Receive', 'Send']:

                pass  # Not a transaction

            else:
                print(f'ERROR: Unhandled line from {fn} => {",".join(row)}')

    return txns
