import datetime
import os.path
import tomllib
import csv
from reckon.constants import TXNS_FILE, TXNS_TOML, STABLECOINS, CONSOLIDATED_FILE, APPROVALS_FILE, SPAM_FILE
from utils import list_to_csv

HEADERS = [
    'date',
    'txn_type',
    'qty',
    'symbol',
    'purchase_token_cost',
    'purchase_token',
    'unit_cost',  # Denominated in the purchase token
    'usd_cost',   # Including fees
    'txn_name',
    'chain',
    'project',
    'wallet',
    'source'
]


def main():
    txns = [HEADERS]
    
    with open(TXNS_TOML, 'rb') as f:
        tf = tomllib.load(f)
    for fn in tf['reports']['coinbase']:
        if os.path.isfile(fn):
            txns.extend(coinbase_txns(fn))
        else:
            print(f'WARN: {fn} from {TXNS_TOML} not found')
    for fn in tf['reports']['coinbasepro']:
        if os.path.isfile(fn):
            txns.extend(coinbasepro_txns(fn))
        else:
            print(f'WARN: {fn} from {TXNS_TOML} not found')
    for fn in tf['reports']['binance']:
        if os.path.isfile(fn):
            txns.extend(binance_txns(fn))
        else:
            print(f'WARN: {fn} from {TXNS_TOML} not found')
    for fn in tf['reports']['blockfi']:
        if os.path.isfile(fn):
            txns.extend(blockfi_txns(fn))
        else:
            print(f'WARN: {fn} from {TXNS_TOML} not found')
    for fn in tf['reports']['manual']:
        if os.path.isfile(fn):
            txns.extend(manual_txns(fn))
        else:
            print(f'WARN: {fn} from {TXNS_TOML} not found')
    
    consolidated, approvals, spam = consolidated_txns()

    txns.extend(consolidated)

    list_to_csv(txns, TXNS_FILE)
    list_to_csv(approvals, APPROVALS_FILE)
    list_to_csv(spam, SPAM_FILE)


def consolidated_txns():
    tx_toml = tomllib.load(open(TXNS_TOML, 'rb'))
    txns = []
    approval_txns = []
    spam_txns = []
    with open(CONSOLIDATED_FILE, 'r') as f:
        next(f)
        lines = 0
        processed_lines = 0
        reader = csv.reader(f)
        for row in reader:
            lines += 1
            [
                number,
                sub,
                cate_id,
                id,
                other_addr,
                other_addr_tag,
                project_id,
                project_name,
                project_chain,
                project_site_url,
                time_at,
                receives_amount,
                receives_from_addr,
                receives_from_addr_tag,
                receives_token_id,
                receives_token_symbol,
                receives_token_is_verified,
                sends_amount,
                sends_to_addr,
                sends_to_addr_tag,
                sends_token_id,
                sends_token_symbol,
                sends_token_is_verified,
                token_approve_spender,
                token_approve_token_id,
                token_approve_token_symbol,
                token_approve_token_is_verified,
                token_approve_value,
                tx_name,
                tx_status,
                tx_from_addr,
                tx_from_addr_tag,
                tx_to_addr,
                tx_to_addr_tag,
                tx_eth_gas_fee,
                tx_usd_gas_fee,
                tx_value,
                tx_params,
                url,
                spam
            ] = row

            if sends_token_id in tx_toml['token_name_overrides']:
                sends_token_symbol = tx_toml['token_name_overrides'][sends_token_id]

            if receives_token_id in tx_toml['token_name_overrides']:
                receives_token_symbol = tx_toml['token_name_overrides'][receives_token_id]
            
            # Test for quick passes
            # TODO Allow for a spam allowlist
            if spam == 'True':
                spam_txns.append(row)
                continue

            elif tx_name == 'approve':
                approval_txns.append(row)
                continue

            elif tx_name == 'transfer':
                # skip
                continue

            # sends_token_symbol = sends_token_symbol.lower()
            # receives_token_symbol = receives_token_symbol.lower()
            if sends_token_symbol.lower() in STABLECOINS and \
                    receives_token_symbol.lower() in STABLECOINS:
                continue  # Stablecoin swap

            if sorted([sends_token_symbol.lower(), 
                receives_token_symbol.lower()]) in \
                    tx_toml['consolidated_parser']['equivalents']:
                continue  # Equivalents swap

            processed_lines += 1
            date = datetime.datetime.fromtimestamp(
                float(time_at)).strftime('%Y-%m-%d %H:%M:%S')

            if sends_token_symbol.lower() != '' and \
                receives_token_symbol.lower() != '':

                if sends_token_symbol.lower() in STABLECOINS:
                    # Buy with stablecoin
                    txns.append([
                        date, 'buy',
                        receives_amount, receives_token_symbol,
                        sends_amount, sends_token_symbol,
                        float(sends_amount) /
                        float(receives_amount), sends_amount,
                        tx_name, project_chain, project_name, tx_from_addr, url
                    ])

                elif receives_token_symbol.lower() in STABLECOINS:
                    # Sell with stablecoin
                    txns.append([
                        date, 'sell',
                        sends_amount, sends_token_symbol,
                        receives_amount, receives_token_symbol,
                        float(receives_amount) /
                        float(sends_amount), receives_amount,
                        tx_name, project_chain, project_name, tx_from_addr, url
                    ])

                else:
                    txns.append([
                        date, 'sell',
                        sends_amount, sends_token_symbol,
                        receives_amount, receives_token_symbol,
                        float(receives_amount)/float(sends_amount), '',
                        tx_name, project_chain, project_name, tx_from_addr, url
                    ])
                    txns.append([
                        date, 'buy',
                        receives_amount, receives_token_symbol,
                        sends_amount, sends_token_symbol,
                        float(sends_amount)/float(receives_amount), '',
                        tx_name, project_chain, project_name, tx_from_addr, url
                    ])

            else:
                if receives_token_symbol.lower() != '' and \
                    tx_name in [
                        'claim',
                        'claim_rewards',
                        'claimAll',
                        'claimAllCTR',
                        'claimFromDistributorViaUniV2EthPair',
                        'claimMulti',
                        'claimReward',
                        'claimRewards',
                        'getReward',
                        'harvest', 
                        'redeem'
                        ]:
                    # Income
                    txns.append([
                        date, 'income',
                        receives_amount, receives_token_symbol,
                        sends_amount, sends_token_symbol,
                        '', '',
                        tx_name, project_chain, project_name, tx_from_addr, url
                    ])

                elif receives_token_symbol.lower() != '' and \
                    tx_toml['config'].get('include_receive', False):
                    txns.append([
                        date, 'receive',
                        receives_amount, receives_token_symbol,
                        0.0, '',
                        0.0, sends_amount,
                        tx_name, project_chain, project_name, tx_from_addr, url
                    ])

                elif tx_toml['config'].get('include_send', False):
                   txns.append([
                        date, 'send',
                        0.0, '',
                        sends_amount, sends_token_symbol,
                        0.0, sends_amount,
                        tx_name, project_chain, project_name, tx_from_addr, url
                    ]) 


    print(f'{processed_lines} / {lines}')
    return txns, approval_txns, spam_txns


def manual_txns(fn):
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
            if tx_type == 'Buy':
                if purchase_token.lower() in STABLECOINS:
                    txns.append([
                        date,
                        'buy',
                        qty, token,
                        purchase_token_qty, purchase_token,
                        float(purchase_token_qty) /
                        float(qty), purchase_token_qty,
                        tx_type, location, location, location, fn
                    ])
    return txns


def coinbase_txns(fn):
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
                    txns.append([date, 'income', qty, asset,
                                 qty_disposed, asset_disposed, '', cost_basis,
                                 txn_type, 'coinbase', 'coinbase', 'coinbase', fn])
            elif txn_type == 'Buy':
                if asset.lower() not in STABLECOINS:
                    txns.append([date, 'buy', qty, asset,
                                 cost_basis, 'USD',
                                 float(cost_basis) / float(qty), cost_basis,
                                 txn_type, 'coinbase', 'coinbase', 'coinbase', fn])
            elif txn_type == 'Converted from':
                from_token = asset_disposed
                from_token_qty = qty_disposed
                row = next(reader)
                [id, txn_type, date, asset, qty, cost_basis, data_source,
                 asset_disposed, qty_disposed, proceeds] = row
                date = f'{date[:10]} {date[11:19]}'

                if from_token.lower() in STABLECOINS:
                    txns.append([date, 'buy', qty, asset,
                                 from_token_qty, from_token,
                                 float(from_token_qty) /
                                 float(qty), cost_basis,
                                 txn_type, 'coinbase', 'coinbase', 'coinbase', fn])
                elif asset.lower() in STABLECOINS:
                    txns.append([date, 'sell', from_token_qty, from_token,
                                 qty, asset, float(
                                     qty) / float(from_token_qty), cost_basis,
                                 txn_type, 'coinbase', 'coinbase', 'coinbase', fn])
                else:
                    txns.append([date, 'sell', from_token_qty, from_token,
                                 qty, asset, float(
                                     qty) / float(from_token_qty), cost_basis,
                                 'Converted from', 'coinbase', 'coinbase', 'coinbase', fn])
                    txns.append([date, 'buy', qty, asset,
                                 from_token_qty, from_token,  float(
                                     from_token_qty) / float(qty), cost_basis,
                                 txn_type, 'coinbase', 'coinbase', 'coinbase', fn])
            elif txn_type in ['Deposit', 'Incoming', 'Receive', 'Send', 'Withdrawal']:
                pass  # Not a transaction
            else:
                print(f'ERROR: Unhandled line from {fn} => {",".join(row)}')

    return txns


def coinbasepro_txns(fn):
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
                        f'{time[:10]} {time[11:19]}', 'buy',
                        next_amount, next_unit,
                        amount, unit,
                        float(amount) / float(next_amount), amount,
                        tx_type, 'coinbasepro', 'coinbasepro', 'coinbasepro', fn
                    ])
                else:
                    print(",".join(row))
            elif tx_type in ['deposit', 'withdrawal']:
                pass
            else:
                print(",".join(row))
    return txns


def binance_txns(fn):
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
                    time, 'buy',
                    realized_amount_quote_asset, quote_asset,
                    realized_amount_base_asset, base_asset,
                    float(realized_amount_base_asset) /
                    float(realized_amount_quote_asset),
                    realized_amount_base_asset,
                    f'{category}/{operation}',
                    'binance', 'binance', 'binance',
                    fn
                ])
            elif category in ['Sell']:
                txns.append([
                    time, 'sell',
                    realized_amount_base_asset, base_asset,
                    realized_amount_quote_asset, quote_asset,
                    float(realized_amount_quote_asset) /
                    float(realized_amount_base_asset),
                    realized_amount_quote_asset,
                    f'{category}/{operation}',
                    'binance', 'binance', 'binance',
                    fn
                ])
            elif category in ['Spot Trading']:
                if operation == 'Buy':
                    if base_asset.lower() not in STABLECOINS:
                        txns.append([
                            time, 'buy',
                            realized_amount_base_asset, base_asset,
                            realized_amount_quote_asset, quote_asset,
                            float(realized_amount_quote_asset) /
                            float(realized_amount_base_asset),
                            realized_amount_quote_asset,
                            f'{category}/{operation}',
                            'binance', 'binance', 'binance',
                            fn
                        ])
                elif operation == 'Sell':
                    if base_asset.lower() not in STABLECOINS:
                        txns.append([
                            time, 'sell',
                            realized_amount_base_asset, base_asset,
                            realized_amount_quote_asset, quote_asset,
                            float(realized_amount_quote_asset) /
                            float(realized_amount_base_asset),
                            realized_amount_quote_asset,
                            f'{category}/{operation}',
                            'binance', 'binance', 'binance',
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


def blockfi_txns(fn):
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
                    usd_cost = f'{float(amount):.8f}' if cryptocurrency.lower(
                    ) in STABLECOINS else ''
                    txns.append([
                        confirmed_at,
                        'income',
                        f'{float(amount):.8f}', cryptocurrency,
                        '', '',
                        '', usd_cost,
                        txn_type, 'blockfi', 'blockfi', 'blockfi', fn
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
                            f'{float(next_amount):.8f}', next_cryptocurrency,
                            abs(float(amount)), cryptocurrency,
                            f'{abs(float(amount))/float(next_amount):.8f}', abs(float(amount)),
                            txn_type, 'blockfi', 'blockfi', 'blockfi', fn
                        ])
                else:
                    if next_cryptocurrency.lower() in STABLECOINS:
                        txns.append([
                            confirmed_at,
                            'sell',
                            f'{float(amount):.8f}', cryptocurrency,
                            next_amount, next_cryptocurrency,
                            f'{float(next_amount)/float(amount):.8f}', '',
                            txn_type, 'blockfi', 'blockfi', 'blockfi', fn
                        ])
                    else:
                        txns.append([
                            confirmed_at,
                            'sell',
                            f'{float(amount):.8f}', cryptocurrency,
                            next_amount, next_cryptocurrency,
                            f'{float(next_amount)/float(amount):.8f}', '',
                            txn_type, 'blockfi', 'blockfi', 'blockfi', fn
                        ])
                        txns.append([
                            confirmed_at,
                            'buy',
                            f'{float(next_amount):.8f}', next_cryptocurrency,
                            amount, cryptocurrency,
                            f'{float(amount)/float(next_amount):.8f}', '',
                            txn_type, 'blockfi', 'blockfi', 'blockfi', fn
                        ])
            else:
                # print(line.rstrip())
                pass
    return txns


if __name__ == '__main__':
    main()
