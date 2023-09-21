import csv
import datetime
from constants import STABLECOINS

def parse(fn):
    
    with open(fn, 'r') as f:
        next(f)
        reader = csv.reader(f)
        
        txns = []
        
        for row in reader:
            if row == []:
                continue

            try:
                if len(row) == 7:
                    [date, received_qty, received_currency, sent_qty, sent_currency, 
                        fee_qty, fee_currency] = row 
                else:
                    [date, received_qty, received_currency, sent_qty, sent_currency, 
                        fee_qty, fee_currency, tag] = row
            except:
                print(f"WARN: Unhandled line in {fn} -> {row}")
                continue

            # Reformat date
            date = datetime.datetime.strptime(date, "%m/%d/%Y %H:%M:%S") \
                .strftime("%Y-%m-%d %H:%M:%S")

            id = f"{fn}{date}"
            for char in "-: /.":
                id = id.replace(char, "")
            
            if sent_qty != "" and received_qty != "":
                # swap
                if received_currency.lower() not in STABLECOINS:
                    txns.append([
                            date,
                            'buy',
                            received_qty, 
                            received_currency,
                            sent_qty, 
                            sent_currency,
                            '', '', '', fn, id         
                        ])

                if sent_currency.lower() not in STABLECOINS:
                    txns.append([
                            date,
                            'sell',
                            sent_qty, 
                            sent_currency,
                            received_qty, 
                            received_currency,
                            '','', '', fn, id
                        ])

            elif received_qty == "":
                txns.append([
                        date,
                        'send',
                        received_qty, 
                        received_currency,
                        sent_qty, 
                        sent_currency,         
                        '','', '', fn, id
                    ])
            
            elif sent_qty == "":
                txns.append([
                        date,
                        'receive',
                        received_qty, 
                        received_currency,
                        sent_qty, 
                        sent_currency,
                        '','', '', fn, id
                    ])
                
    return txns
