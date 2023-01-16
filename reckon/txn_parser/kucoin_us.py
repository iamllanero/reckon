import csv
from txns import txline
from datetime import datetime

def parse(fn):
    """
    Parser for KuCoin US reports. Note that KuCoin reports may come in Excel
    format. Be sure to export as CSV to use with this parser.
    """
    print(f"processing {fn} in kucoin_us")
    txns = []
    with open(fn, 'r') as f:
        next(f)
        reader = csv.reader(f)
        for row in reader:
            [
                uid,
                account_type,
                order_id,
                order_time,
                symbol,
                side,
                order_type,
                order_price,
                order_amount,
                avg_filled_price,
                filled_amount,
                filled_volume,
                filled_volume_usd,
                filled_time,
                fee,
                fee_currency,
                status,
            ] = row
            txns.append(txline(side.lower(),{
                'time_at': datetime.strptime(order_time, '%Y-%m-%d %H:%M:%S').timestamp(),
                'receives.amount': order_amount,
                'receives.token.symbol': symbol.split('-')[0],
                'sends.amount': filled_volume_usd,
                'sends.token.symbol': symbol.split('-')[1],
                'tx.name': f'{side}-{order_type}',
                'project.chain': 'kucoin_us',
                'project.name': 'kucoin_us' ,
                'tx.from_addr': f'kucoin_us-{uid[4:]}',
                'id': order_id,
                'url': '',
            }))

    return txns