import csv
from config import STABLECOINS

def parse(fn):
    txns = []
    with open(fn, 'r') as f:
        next(f)
        reader = csv.reader(f)
        for row in reader:
            """
            User_Id,
            Time,
            Category,
            Operation,
            Order_Id,
            Transaction_Id,
            Primary_Asset,                        # DEPOSITS/WITHDRAWALS/REWARDS
            Realized_Amount_For_Primary_Asset,
            Realized_Amount_For_Primary_Asset_In_USD_Value,
            Base_Asset,                           # WHAT I'M BUYING WITH
            Realized_Amount_For_Base_Asset,
            Realized_Amount_For_Base_Asset_In_USD_Value,
            Quote_Asset,                          # WHAT I'M BUYING
            Realized_Amount_For_Quote_Asset,
            Realized_Amount_For_Quote_Asset_In_USD_Value,
            Fee_Asset,
            Realized_Amount_For_Fee_Asset,
            Realized_Amount_For_Fee_Asset_In_USD_Value,
            Payment_Method,
            Withdrawal_Method,
            Additional_Note
            """
            [user_id, time, category, operation, order_id, txn_id,
             primary_asset, realized_amount_primary_asset, realized_amount_primary_asset_usd,
             base_asset, realized_amount_base_asset, realized_amount_base_asset_usd,
             quote_asset, realized_amount_quote_asset, realized_amount_quote_asset_usd,
             fee_asset, realized_amount_fee_asset, realized_amount_fee_asset_usd,
             payment_method, withdrawal_method, addl_notes
             ] = row

            time = f'{time[:19]}'

            if operation in ['Staking Rewards']:
                # txns.append([time, txn_id, fn])
                pass
            elif category in ['Buy']:
                txns.append([
                    time, 
                    'buy',
                    realized_amount_quote_asset, 
                    quote_asset,
                    realized_amount_base_asset, 
                    base_asset,
                    # float(realized_amount_base_asset) / float(realized_amount_quote_asset),
                    # realized_amount_base_asset,
                    f'{category}/{operation}',
                    'binance', 
                    'binance', 
                    '',
                    '',
                    '',
                    fn
                ])
            elif category in ['Sell']:
                txns.append([
                    time, 
                    'sell',
                    realized_amount_base_asset, 
                    base_asset,
                    realized_amount_quote_asset, 
                    quote_asset,
                    # float(realized_amount_quote_asset) / float(realized_amount_base_asset),
                    # realized_amount_quote_asset,
                    f'{category}/{operation}',
                    'binance', 
                    'binance', 
                    '',
                    '',
                    '',
                    fn
                ])
            elif category in ['Spot Trading']:
                if operation == 'Buy':
                    if base_asset.lower() not in STABLECOINS:
                        txns.append([
                            time, 
                            'buy',
                            realized_amount_base_asset, 
                            base_asset,
                            realized_amount_quote_asset, 
                            quote_asset,
                            # float(realized_amount_quote_asset) / float(realized_amount_base_asset),
                            # realized_amount_quote_asset,
                            f'{category}/{operation}',
                            'binance', 
                            'binance', 
                            '',
                            '',
                            '',
                            fn
                        ])
                elif operation == 'Sell':
                    if base_asset.lower() not in STABLECOINS:
                        txns.append([
                            time, 
                            'sell',
                            realized_amount_base_asset, 
                            base_asset,
                            realized_amount_quote_asset, 
                            quote_asset,
                            # float(realized_amount_quote_asset) / float(realized_amount_base_asset),
                            # realized_amount_quote_asset,
                            f'{category}/{operation}',
                            'binance', 
                            'binance', 
                            '',
                            '',
                            '',
                            fn
                        ])
                else:
                    print(
                        f'ERROR: Unhandled line from {fn} => {",".join(row)}')
            elif category in ['Deposit', 'Withdrawal']:
                pass  # Not a transaction
            else:
                print(f'ERROR: Unhandled line from {fn} => {",".join(row)}')

            # results = line.rstrip().split(',')
            # txns.append(results)
    return txns
