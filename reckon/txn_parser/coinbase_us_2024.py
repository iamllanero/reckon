import csv
import re
from config import STABLECOINS

# Headers from the latest coinbase reports (for 2023)

# ID,
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
        # Skip first 4 lines
        next(f)
        next(f)
        next(f)
        next(f)
        reader = csv.reader(f)
        for row in reader:
            [
                id,
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
            # Strip first char from currency values
            cost_basis = cost_basis[1:]
            fee = fee[1:]
            # If qty starts with '-', remove it
            if qty.startswith('-'):
                qty = qty[1:]

            if txn_type in ['Reward Income', 'Staking Income']:
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
                        f'{fn}:{id}'
                    ])

            elif txn_type == 'Buy' or txn_type == 'Advanced Trade Buy':

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
                        f'{fn}:{id}'
                    ])

            elif txn_type == 'Sell' or txn_type == 'Advanced Trade Sell':
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
                        f'{fn}:{id}'
                    ])

            elif txn_type in ['Receive', 'Send', 'Deposit', 'Convert', 'Withdrawal', 'Subscription Rebates (24 Hours)']:

                pass  # Not a transaction

            else:
                print(f'ERROR: Unhandled line from {fn} => {",".join(row)}')

    return txns
