import csv
from config import STABLECOINS

def parse(fn):
    txns = []
    with open(fn, 'r') as f:
        next(f)
        reader = csv.reader(f)
        for row in reader:
            [cryptocurrency, amount, txn_type,
                confirmed_at] = row
            if txn_type in ['Interest Payment', 'Bonus Payment']:
                if cryptocurrency.lower() in STABLECOINS and float(amount) < 0.50:
                    pass  # No need to track below $0.50
                else:
                    txns.append([
                        confirmed_at,
                        'income',
                        f'{float(amount):.8f}', 
                        cryptocurrency,
                        '', 
                        '',
                        '', 
                        '',
                        'blockfi', 
                        'blockfi', 
                        txn_type, 
                        '',
                        fn
                    ])
            elif txn_type == 'Trade':
                [next_cryptocurrency, next_amount, next_txn_type,
                    next_confirmed_at] = next(reader)
                if cryptocurrency.lower() in STABLECOINS:
                    if next_cryptocurrency.lower() in STABLECOINS:
                        pass  # This is a stablecoin swap
                    else:
                        txns.append([
                            confirmed_at,
                            'buy',
                            f'{float(next_amount):.8f}', 
                            next_cryptocurrency,
                            '', 
                            abs(float(amount)), 
                            cryptocurrency,
                            '',
                            'blockfi', 
                            'blockfi', 
                            txn_type, 
                            '',
                            fn
                        ])
                else:
                    if next_cryptocurrency.lower() in STABLECOINS:
                        txns.append([
                            confirmed_at,
                            'sell',
                            f'{float(amount):.8f}', 
                            cryptocurrency,
                            '', 
                            next_amount, 
                            next_cryptocurrency,
                            '',
                            'blockfi', 
                            'blockfi', 
                            txn_type,
                            '',
                            fn
                        ])
                    else:
                        txns.append([
                            confirmed_at,
                            'sell',
                            f'{float(amount):.8f}', 
                            cryptocurrency,
                            '', 
                            next_amount, 
                            next_cryptocurrency,
                            '',
                            'blockfi', 
                            'blockfi', 
                            txn_type, 
                            '',
                            fn
                        ])
                        txns.append([
                            confirmed_at,
                            'buy',
                            f'{float(next_amount):.8f}', 
                            next_cryptocurrency,
                            '', 
                            amount, 
                            cryptocurrency,
                            '',
                            'blockfi', 
                            'blockfi', 
                            txn_type, 
                            '',
                            fn
                        ])
            else:
                pass
    return txns
