import csv
import datetime
import os.path
import sys

import tomlkit
import tomllib
from reckon.constants import (APPROVALS_FILE, CONSOLIDATED_FILE, SPAM_FILE,
                              STABLECOINS, TXNS_FILE, TXNS_TOML)
from config import TXNS_CONFIG, TAGS, TXN_OVERRIDES, TRANSACTION_OVERRIDES_FILE
from reckon.debank import FLAT_HEADERS
from reckon.utils import list_to_csv

HEADERS = [
    'date',
    'txn_type',
    'qty',
    'symbol',
    'purchase_token_cost',
    'purchase_token',
    'txn_name',
    'chain',
    'project',
    'wallet',
    'id',
    'url',
]

# TODO Change report processing to use tx_line (and maybe externalize)

def main():
    txns = [HEADERS]

    for fn in TXNS_CONFIG['reports']['coinbase']:
        if os.path.isfile(fn):
            txns.extend(coinbase_txns(fn))
        else:
            print(f'WARN: {fn} from {TXNS_TOML} not found')
    for fn in TXNS_CONFIG['reports']['coinbasepro']:
        if os.path.isfile(fn):
            txns.extend(coinbasepro_txns(fn))
        else:
            print(f'WARN: {fn} from {TXNS_TOML} not found')
    for fn in TXNS_CONFIG['reports']['binance']:
        if os.path.isfile(fn):
            txns.extend(binance_txns(fn))
        else:
            print(f'WARN: {fn} from {TXNS_TOML} not found')
    for fn in TXNS_CONFIG['reports']['blockfi']:
        if os.path.isfile(fn):
            txns.extend(blockfi_txns(fn))
        else:
            print(f'WARN: {fn} from {TXNS_TOML} not found')
    for fn in TXNS_CONFIG['reports']['manual']:
        if os.path.isfile(fn):
            txns.extend(manual_txns(fn))
        else:
            print(f'WARN: {fn} from {TXNS_TOML} not found')
    
    consolidated, approvals, spam = consolidated_txns()

    txns.extend(consolidated)

    list_to_csv(txns, TXNS_FILE)
    list_to_csv(approvals, APPROVALS_FILE)
    list_to_csv(spam, SPAM_FILE)


def txline(txn_type, txn_dict):
    show_tags = TXNS_CONFIG['output'].get("show_tags", False)
    
    date = datetime.datetime.fromtimestamp(
        float(txn_dict['time_at'])).strftime('%Y-%m-%d %H:%M:%S')

    return [
        date, 
        txn_type,
        txn_dict['receives.amount'],
        txn_dict['receives.token.symbol'],
        txn_dict['sends.amount'],
        txn_dict['sends.token.symbol'],
        txn_dict['tx.name'], 
        txn_dict['project.chain'],
        txn_dict['project.name'], 
        txn_dict['tx.from_addr'] if not show_tags else \
            TAGS.get(txn_dict['tx.from_addr'], txn_dict['tx.from_addr']), 
        txn_dict['id'],
        txn_dict['url'],
    ]


def process_batch(txn_dicts, do_overrides=True):
    txns = []

    if txn_dicts[0]['id'] in TXN_OVERRIDES.keys() and do_overrides:
        # This transaction id has an override entry.  Generate lines
        # directly from override data
        for txline_data in TXN_OVERRIDES[txn_dicts[0]['id']]:
            tl = []
            for header in HEADERS:
                tl.append(txline_data[header])
            txns.append(tl)

        return txns
    
    if len(txn_dicts) > 1:
        # use averages to calculate multi-token LP deposit or withdrawals

        send_amounts = [float(i['sends.amount']) if i['sends.amount'] else 0.0 \
            for i in txn_dicts]
        recv_amounts = [float(i['receives.amount']) if i['receives.amount'] else 0.0 \
            for i in txn_dicts]

        nonzero_sends = sum([1 for i in send_amounts if i > 0])
        nonzero_recvs = sum([1 for i in recv_amounts if i > 0])

        if nonzero_sends == 1 and nonzero_recvs == len(txn_dicts):
            # One token was sent, multiple were received back
            for td in txn_dicts:
                td['sends.token.symbol'] = txn_dicts[0]['sends.token.symbol']
                td['sends.amount'] = sum(send_amounts) / float(len(send_amounts))

        if nonzero_recvs == 1 and nonzero_sends == len(txn_dicts):
            # Multiple tokens were sent, one was received back
            for td in txn_dicts:
                td['receives.token.symbol'] = txn_dicts[0]['receives.token.symbol']
                td['receives.amount'] = sum(recv_amounts) / float(len(recv_amounts))
            
    for td in txn_dicts:
        sends_token = td['sends.token.symbol'].lower()
        receives_token = td['receives.token.symbol'].lower()

        if sends_token != '' and receives_token != '':
            # swap of some kind

            if receives_token not in STABLECOINS:
                # If not selling to stables, include a "buy" transaction
                txns.append(txline('buy', td))

            if sends_token not in STABLECOINS:
                # If not buying w/stables, include a "sell" transaction

                # If neither is a stablecoin (swap), invert send/recv for sell txn
                if receives_token not in STABLECOINS:
                    td['receives.amount'], td['sends.amount'] = \
                        td['sends.amount'], td['receives.amount']
                    td['receives.token.symbol'], td['sends.token.symbol'] = \
                        td['sends.token.symbol'], td['receives.token.symbol']

                txns.append(txline('sell', td))

        elif sends_token == '' and receives_token == '':
            # no tokens sent or received
            pass

        else:
            if receives_token != '' and td['tx.name'] in [
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
                txns.append(txline('income', td))

            elif receives_token != '' and \
                TXNS_CONFIG['output']['include_receive']:
                txns.append(txline('receive', td))

            elif TXNS_CONFIG['output']['include_send']:
                txns.append(txline('send', td))

    return txns


def consolidated_txns():
    txns = []
    approval_txns = []
    spam_txns = []
    
    with open(CONSOLIDATED_FILE, 'r') as f:
        next(f)
        lines = 0
        processed_lines = 0
        reader = csv.reader(f)
        txn_batch = []
        for row in reader:
            lines += 1
            txn_dict = dict(zip(FLAT_HEADERS, row))
            # Test for quick passes
            # TODO Allow for a spam allowlist
            if txn_dict['spam'] == 'True':
                spam_txns.append(row)
                continue

            elif txn_dict['tx.name'] == 'approve':
                approval_txns.append(row)
                continue

            if txn_dict['sends.token_id'] in TXNS_CONFIG['token_name_overrides']:
                txn_dict['sends.token.symbol'] = \
                    TXNS_CONFIG['token_name_overrides'][txn_dict['sends.token_id']]

            if txn_dict['receives.token_id'] in TXNS_CONFIG['token_name_overrides']:
                txn_dict['receives.token.symbol'] = \
                    TXNS_CONFIG['token_name_overrides'][txn_dict['receives.token_id']]

            if txn_dict['sends.token.symbol'].lower() in STABLECOINS and \
                    txn_dict['receives.token.symbol'].lower() in STABLECOINS:
                continue  # Stablecoin swap

            if sorted([txn_dict['sends.token.symbol'].lower(), 
                txn_dict['receives.token.symbol'].lower()]) in \
                    TXNS_CONFIG['consolidated_parser']['equivalents']:
                continue  # Equivalents swap

            processed_lines += 1
    
            if txn_dict['sub'] != '0':
                txn_batch.append(txn_dict)

            elif len(txn_batch) > 0:
                txns.extend(process_batch(txn_batch))
                txn_batch = [txn_dict]

            else:
                # First transaction
                txn_batch = [txn_dict]

        # Last transaction(s)    
        txns.extend(process_batch(txn_batch))


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
                        'coinbase',
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
                        'coinbase', 
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
                        'coinbase', 
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
                        'coinbase', 
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
                        'coinbase', 
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
                        'coinbase', 
                        fn
                    ])
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
                        'coinbasepro', 
                        fn
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
                    'binance',
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
                    'binance',
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
                            'binance',
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
                            'binance',
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

def cmd_init_override(ids_to_override):
    for _id in ids_to_override:
        
        # Retrieve relevant lines from consolidated
        with open(CONSOLIDATED_FILE, 'r') as f:
            next(f)
            reader = csv.reader(f)
            txn_batch = []

            for row in reader:
                txn_dict = dict(zip(FLAT_HEADERS, row))

                if txn_dict['id'] == _id:
                    txn_batch.append(txn_dict)

        # Generate txn_lines as dict corresponding to standard output
        std_txlines = process_batch(txn_batch, False)
        std_txlines_d = [dict(zip(HEADERS, i)) for i in std_txlines]

        # Write (or overwrite) these data to TXN_OVERRIDES_FILE
        with open(TRANSACTION_OVERRIDES_FILE, 'rb') as f:
            overrides = tomlkit.parse(f.read())
            if len(overrides) == 0:
                # TODO make a nicer more descriptive set of instructions
                overrides.add(tomlkit.comment("Default values shown as comments."))

        if _id in overrides.keys():
            #  WARNING:  this depends on the order of subtransactions in consolidated and txns being consistent
            print(f"WARN: Overwriting existing override entry for {_id} with defaults.")
            for src, dest in zip(std_txlines_d, overrides[_id]):
                for k,v in src.items():
                    dest[k] = v
        else:
            # Generate new tx group entry with comments.
            # overrides.add_line()
            overrides.add(tomlkit.ws("\n"))
            overrides.add(tomlkit.comment("########################################################################"))
            overrides.add(tomlkit.comment("#########################   NEW TX GROUP   #############################"))
            overrides.add(tomlkit.comment("########################################################################"))
            container = tomlkit.aot()

            for entry in std_txlines_d:
                toml = tomlkit.table()
                
                for k,v in entry.items():
                    toml.add(k, v)
                    toml[k].comment(v)

                # toml.append(_id, toml)
                container.append(toml)
            
            overrides.append(_id, container)
            
        with open(TRANSACTION_OVERRIDES_FILE, "wt") as f:
            tomlkit.dump(overrides, f)
            print(f"Updated {TRANSACTION_OVERRIDES_FILE}")

if __name__ == '__main__':

    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        if cmd == 'init_override':
            cmd_init_override(sys.argv[2:])
    else:
        main()
