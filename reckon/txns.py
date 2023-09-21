import csv
import datetime
import importlib
import os.path
# import sys

# import tomlkit
from constants import (APPROVALS_FILE, CONSOLIDATED_FILE, SPAM_FILE,
                              STABLECOINS, TXNS_FILE, TXNS_TOML)
from config import TXNS_CONFIG, TAGS, TXN_OVERRIDES, TRANSACTION_OVERRIDES_FILE
from debank import FLAT_HEADERS
from utils import list_to_csv

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

def parse_report(fn, parser):
    if not os.path.isfile(fn):
        print(f'WARN: {fn} from {TXNS_TOML} not found')
        return []

    module = importlib.import_module(f'txn_parser.{parser}')
    method = getattr (module, "parse")
    return method(fn)

# TODO Change report processing to use tx_line (and maybe externalize)

def sort_except(list, ignore):
    temp = list.pop(ignore)
    list.sort(key= lambda x: datetime.datetime.strptime(x[0], '%Y-%m-%d %H:%M:%S'))
    list.insert(ignore, temp)

def main():
    txns = [HEADERS]

    consolidated, approvals, spam = consolidated_txns()
    txns.extend(consolidated)

    reports = TXNS_CONFIG['reports']
    for key in reports.keys():
        print(f'Processing {key} with {reports[key]}')
        no_lines = len(txns)
        txns.extend(
            parse_report(
                reports[key]['file'],
                reports[key]['parser'],
                )
        )
        print(f'Added {len(txns) - no_lines} entries')
   
    # Sort output data for easier reading
    sort_except(txns, 0)
    
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


# def cmd_init_override(ids_to_override):
#     for _id in ids_to_override:
        
#         # Retrieve relevant lines from consolidated
#         with open(CONSOLIDATED_FILE, 'r') as f:
#             next(f)
#             reader = csv.reader(f)
#             txn_batch = []

#             for row in reader:
#                 txn_dict = dict(zip(FLAT_HEADERS, row))

#                 if txn_dict['id'] == _id:
#                     txn_batch.append(txn_dict)

#         # Generate txn_lines as dict corresponding to standard output
#         std_txlines = process_batch(txn_batch, False)
#         std_txlines_d = [dict(zip(HEADERS, i)) for i in std_txlines]

#         # Write (or overwrite) these data to TXN_OVERRIDES_FILE
#         with open(TRANSACTION_OVERRIDES_FILE, 'rb') as f:
#             overrides = tomlkit.parse(f.read())
#             if len(overrides) == 0:
#                 # TODO make a nicer more descriptive set of instructions
#                 overrides.add(tomlkit.comment("Default values shown as comments."))

#         if _id in overrides.keys():
#             #  WARNING:  this depends on the order of subtransactions in consolidated and txns being consistent
#             print(f"WARN: Overwriting existing override entry for {_id} with defaults.")
#             for src, dest in zip(std_txlines_d, overrides[_id]):
#                 for k,v in src.items():
#                     dest[k] = v
#         else:
#             # Generate new tx group entry with comments.
#             # overrides.add_line()
#             overrides.add(tomlkit.ws("\n"))
#             overrides.add(tomlkit.comment("########################################################################"))
#             overrides.add(tomlkit.comment("#########################   NEW TX GROUP   #############################"))
#             overrides.add(tomlkit.comment("########################################################################"))
#             container = tomlkit.aot()

#             for entry in std_txlines_d:
#                 toml = tomlkit.table()
                
#                 for k,v in entry.items():
#                     toml.add(k, v)
#                     toml[k].comment(v)

#                 # toml.append(_id, toml)
#                 container.append(toml)
            
#             overrides.append(_id, container)
            
#         with open(TRANSACTION_OVERRIDES_FILE, "wt") as f:
#             tomlkit.dump(overrides, f)
#             print(f"Updated {TRANSACTION_OVERRIDES_FILE}")

if __name__ == '__main__':

    # if len(sys.argv) > 1:
    #     cmd = sys.argv[1]
    #     if cmd == 'init_override':
    #         cmd_init_override(sys.argv[2:])
    # else:
    #     main()

    main()