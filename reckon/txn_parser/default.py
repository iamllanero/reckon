import csv
from reckon.constants import STABLECOINS

def parse(fn):
    """
    NOTE: This parser currently only handles buy transactions in stablecoins.
    """
    txns = []
    with open(fn, 'r') as f:
        next(f)
        reader = csv.reader(f)
        for row in reader:
            [date, tx_type, token, qty, purchase_token, purchase_token_qty,
                fees, usd, location, id] = row
            if tx_type.lower() == 'buy':
                if purchase_token.lower() in STABLECOINS:
                    txns.append([
                        date,
                        'buy',
                        qty, 
                        token,
                        purchase_token_qty, 
                        purchase_token,
                        # float(purchase_token_qty) / float(qty), 
                        # purchase_token_qty,
                        tx_type, 
                        location, 
                        location, 
                        location, 
                        fn
                    ])
    return txns
