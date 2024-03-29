import csv
from config import STABLECOINS

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
            
            if id == "": 
                # generate an id for this tx
                id = "".join([c for c in date if c not in "-:/ "])
                id += "".join([c for c in fn if c not in "/"])

            if tx_type.lower() == 'buy':
                if purchase_token.lower() in STABLECOINS:
                    txns.append([
                        date,
                        'buy',
                        qty, 
                        token,
                        '', # token_id
                        purchase_token_qty, 
                        purchase_token,
                        '', # purchase_token_id
                        location, 
                        location, 
                        tx_type, 
                        fn,
                        id,
                    ])
    return txns
