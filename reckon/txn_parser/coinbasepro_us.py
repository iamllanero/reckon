import csv
from config import STABLECOINS

def parse(fn):
    """
    Parses Coinbase Pro report.

    NOTE: that this parser does not handle anything other than buy orders at 
    this time. Since CBP is being deprecated, and not used by me, I won't 
    bother to make this more robust.
    """
    txns = []
    with open(fn, 'r') as f:
        next(f)
        reader = csv.reader(f)
        for row in reader:
            [portfolio, tx_type, time, amount, balance, unit,
                transfer_id, trade_id, order_id] = row
            if tx_type == 'match':
                [portfolio, tx_type, time, next_amount, next_balance, next_unit,
                    transfer_id, trade_id, order_id] = next(reader)
                [portfolio, fee_tx_type, time, fee_amount, fee_balance, fee_unit,
                    transfer_id, trade_id, order_id] = next(reader)
                amount = float(amount) * -1
                if unit.lower() in STABLECOINS:
                    txns.append([
                        f'{time[:10]} {time[11:19]}', 
                        'buy',
                        next_amount, 
                        next_unit,
                        amount, 
                        unit,
                        # float(amount) / float(next_amount), 
                        # amount,
                        tx_type, 
                        'coinbasepro', 
                        'coinbasepro', 
                        '', 
                        '',
                        '',
                        fn
                    ])
                else:
                    print(",".join(row))
            elif tx_type in ['deposit', 'withdrawal']:
                pass
            else:
                print(",".join(row))
    return txns
