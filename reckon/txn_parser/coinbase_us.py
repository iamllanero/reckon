import csv
from config import STABLECOINS

def parse(fn):
    txns = []
    with open(fn, 'r') as f:
        next(f)
        reader = csv.reader(f)
        for row in reader:
            [id, txn_type, date, asset, qty, cost_basis, data_source,
             asset_disposed, qty_disposed, proceeds] = row

            date = f'{date[:10]} {date[11:19]}'

            if txn_type in ['Reward', 'Interest', 'Fork']:
                if float(cost_basis) > 0.40:
                    txns.append([
                        date, 
                        'income', 
                        qty, 
                        asset,
                        qty_disposed, 
                        asset_disposed,
                        # '', 
                        # cost_basis,
                        txn_type,
                        'coinbase',
                        'coinbase',
                        '',
                        '',
                        '',
                        fn
                    ])
            elif txn_type == 'Buy':
                if asset.lower() not in STABLECOINS:
                    txns.append([
                        date,
                        'buy', 
                        qty, 
                        asset,
                        cost_basis, 
                        'USD',
                        # float(cost_basis) / float(qty), 
                        # cost_basis,
                        txn_type,
                        'coinbase', 
                        'coinbase', 
                        '', 
                        '',
                        '',
                        fn
                    ])
            elif txn_type == 'Converted from':
                from_token = asset_disposed
                from_token_qty = qty_disposed
                row = next(reader)
                [id, txn_type, date, asset, qty, cost_basis, data_source,
                 asset_disposed, qty_disposed, proceeds] = row
                date = f'{date[:10]} {date[11:19]}'

                if from_token.lower() in STABLECOINS:
                    txns.append([
                        date, 
                        'buy', 
                        qty, 
                        asset,
                        from_token_qty, 
                        from_token,
                        # float(from_token_qty) / float(qty), 
                        # cost_basis,
                        txn_type, 
                        'coinbase', 
                        'coinbase', 
                        '', 
                        '',
                        '',
                        fn
                    ])
                elif asset.lower() in STABLECOINS:
                    txns.append([
                        date, 
                        'sell', 
                        from_token_qty, 
                        from_token,
                        qty, asset, 
                        # float(qty) / float(from_token_qty), 
                        # cost_basis,
                        txn_type, 
                        'coinbase', 
                        'coinbase', 
                        '', 
                        '',
                        '',
                        fn
                    ])
                else:
                    txns.append([
                        date, 
                        'sell', 
                        from_token_qty, 
                        from_token,
                        qty, 
                        asset, 
                        # float(qty) / float(from_token_qty), 
                        # cost_basis,
                        'Converted from', 
                        'coinbase', 
                        'coinbase', 
                        '', 
                        '',
                        '',
                        fn
                    ])
                    txns.append([
                        date, 
                        'buy', 
                        qty, 
                        asset,
                        from_token_qty, 
                        from_token,  
                        # float(from_token_qty) / float(qty), 
                        # cost_basis,
                        txn_type, 
                        'coinbase', 
                        'coinbase', 
                        '', 
                        '',
                        '',
                        fn
                    ])
            elif txn_type in ['Deposit', 'Incoming', 'Receive', 'Send', 'Withdrawal']:
                pass  # Not a transaction
            else:
                print(f'ERROR: Unhandled line from {fn} => {",".join(row)}')

    return txns
