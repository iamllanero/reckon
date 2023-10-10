import csv
import re
from config import STABLECOINS

# Headers from the latest coinbase reports (as of 2021-10-10)

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
            elif txn_type == 'Buy':
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
            elif txn_type == 'Convert':
                # Convert the listed assets to the purchase token
                from_token = symbol
                from_token_qty = qty

                # Extract the tokens actually purchased from the notes field
                match = re.search(r"to ([\d,]+\.?\d*) (\w+)", notes)
                if match:
                    qty = float(match.group(1).replace(',', ''))  # Remove commas and convert to float
                    symbol = match.group(2)                
                else:
                    print(f"- ERROR: Pattern not found in the notes {notes}.")

                # If from_token is a stablecoin, then this is a buy

                if from_token.lower() in STABLECOINS:
                    txns.append([
                        date,
                        'buy',
                        qty,
                        symbol,
                        '',
                        from_token_qty,
                        from_token,
                        '',
                        'coinbase',
                        'coinbase',
                        txn_type,
                        '',
                        fn
                    ])

                # If the to_token is a stablecoin, then this is a sell
                elif symbol.lower() in STABLECOINS:
                    txns.append([
                        date,
                        'sell',
                        from_token_qty,
                        from_token,
                        '',
                        qty,
                        symbol,
                        '',
                        'coinbase',
                        'coinbase',
                        txn_type,
                        '',
                        fn
                    ])

                # Otherwise, this is a buy and a sell
                else:
                    txns.append([
                        date,
                        'sell',
                        from_token_qty,
                        from_token,
                        '',
                        qty,
                        symbol,
                        '',
                        'coinbase',
                        'coinbase',
                        txn_type,
                        '',
                        fn
                    ])
                    txns.append([
                        date,
                        'buy',
                        qty,
                        symbol,
                        '',
                        from_token_qty,
                        from_token,
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
