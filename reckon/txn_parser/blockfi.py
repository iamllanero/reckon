import csv
from reckon.constants import STABLECOINS

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
                        # '', 
                        txn_type, 
                        'blockfi', 
                        'blockfi', 
                        'blockfi', 
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
                            abs(float(amount)), 
                            cryptocurrency,
                            # f'{abs(float(amount))/float(next_amount):.8f}', 
                            # abs(float(amount)),
                            txn_type, 
                            'blockfi', 
                            'blockfi', 
                            'blockfi', 
                            fn
                        ])
                else:
                    if next_cryptocurrency.lower() in STABLECOINS:
                        txns.append([
                            confirmed_at,
                            'sell',
                            f'{float(amount):.8f}', 
                            cryptocurrency,
                            next_amount, 
                            next_cryptocurrency,
                            # f'{float(next_amount)/float(amount):.8f}', 
                            # '',
                            txn_type,
                            'blockfi', 
                            'blockfi', 
                            'blockfi', 
                            fn
                        ])
                    else:
                        txns.append([
                            confirmed_at,
                            'sell',
                            f'{float(amount):.8f}', 
                            cryptocurrency,
                            next_amount, 
                            next_cryptocurrency,
                            # f'{float(next_amount)/float(amount):.8f}', 
                            # '',
                            txn_type, 
                            'blockfi', 
                            'blockfi', 
                            'blockfi', 
                            fn
                        ])
                        txns.append([
                            confirmed_at,
                            'buy',
                            f'{float(next_amount):.8f}', 
                            next_cryptocurrency,
                            amount, 
                            cryptocurrency,
                            # f'{float(amount)/float(next_amount):.8f}', 
                            # '',
                            txn_type, 
                            'blockfi', 
                            'blockfi', 
                            'blockfi', 
                            fn
                        ])
            else:
                # print(line.rstrip())
                pass
    return txns
