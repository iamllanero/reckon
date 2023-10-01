import csv
import datetime
import importlib
import os.path
# import sys

# import tomlkit
from config import (
    APPROVALS_OUTPUT, 
    FLATTEN_OUTPUT, 
    SPAM_OUTPUT,
    STABLECOINS_OUTPUT,
    EQUIVALENTS_OUTPUT,
    EMPTY_OUTPUT,
    STABLECOINS, 
    TXNS_OUTPUT, 
    TXNS_PRICE_REQ_OUTPUT,
    TXNS_TOML,
    TXNS_CONFIG, 
    TAGS, 
    TXN_OVERRIDES, 
    # TRANSACTION_OVERRIDES_FILE
    )
from debank import FLAT_HEADERS
# from utils import list_to_csv

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
    'token_id',
    'purchase_token_id',
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


def write_csv(list, file_path):
    with open(file_path, 'w', newline='') as csvfile:
        csvwriter = csv.writer(csvfile)
        csvwriter.writerows(list)


def create_price_requests(txns):
    requests = []
    for txn in txns:
        txn_dict = dict(zip(HEADERS, txn))
        if txn_dict['txn_type'] in ['buy', 'sell', 'income']:
            requests.append([
                txn_dict['date'],
                txn_dict['chain'],
                txn_dict['symbol'],
                txn_dict['token_id'],
                txn_dict['txn_type'],
            ])
    write_csv(requests, TXNS_PRICE_REQ_OUTPUT)


def main():
    txns = [HEADERS]

    (consolidated, 
     approval_txns, 
     spam_txns, 
     stable_txns, 
     equivalent_txns,
     empty_txns) = consolidated_txns()
    
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
    
    write_csv(txns, TXNS_OUTPUT)
    write_csv(approval_txns, APPROVALS_OUTPUT)
    write_csv(spam_txns, SPAM_OUTPUT)
    write_csv(stable_txns, STABLECOINS_OUTPUT)
    write_csv(equivalent_txns, EQUIVALENTS_OUTPUT)
    write_csv(empty_txns, EMPTY_OUTPUT)

    create_price_requests(txns)


def txline(txn_type, txn_dict):
    show_tags = TXNS_CONFIG['output'].get("show_tags", False)
    
    date = datetime.datetime.fromtimestamp(
        float(txn_dict['time_at'])).strftime('%Y-%m-%d %H:%M:%S')
    # print(txn_dict)
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
        txn_dict['receives.token_id'] if 'receives.token_id' in txn_dict else '',
        txn_dict['sends.token_id'] if 'send.token_id' in txn_dict else '',
        txn_dict['id'],
        txn_dict['url'],
    ]

# TODO Remove the optionality to include overrides as well as unknown receives
#      and sends
def process_batch(txn_dicts, do_overrides=True):
    """
    Process a transaction batch, creating sell and buy transactions as needed.

    This function contains the main logic for categorizing transactions as
    buys, sells, income, etc. It assumes pre-processing has been done in the
    consolidated_txns() function to remove spam, approvals, etc.
    """

    txns = []

    # If transaction id has an override entry, generate lines directly from it
    if txn_dicts[0]['id'] in TXN_OVERRIDES.keys() and do_overrides:
        for txline_data in TXN_OVERRIDES[txn_dicts[0]['id']]:
            tl = []
            for header in HEADERS:
                tl.append(txline_data[header])
            txns.append(tl)

        return txns

    # If multi-line txn, use average to calculate deposit and withdrawals
    if len(txn_dicts) > 1:
    
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

    # Generate transaction line(s) for each transaction in batch
    for td in txn_dicts:
        sends_token = td['sends.token.symbol'].lower()
        receives_token = td['receives.token.symbol'].lower()

        # If both are filled, must be a swap of some kind. Unless one side is
        # a stablecoin, this means both a buy and sell transaction
        if sends_token != '' and receives_token != '':

            # If not selling to stables, include "buy" transaction
            if receives_token not in STABLECOINS:
                txns.append(txline('buy', td))

            # If not buying w/stables, include "sell" transaction
            if sends_token not in STABLECOINS:

                # If neither is a stablecoin (swap), invert send/recv for sell txn
                if receives_token not in STABLECOINS:
                    td['receives.amount'], td['sends.amount'] = \
                        td['sends.amount'], td['receives.amount']
                    td['receives.token.symbol'], td['sends.token.symbol'] = \
                        td['sends.token.symbol'], td['receives.token.symbol']
                    td['receives.token_id'], td['sends.token_id'] = \
                        td['sends.token_id'], td['receives.token_id']

                txns.append(txline('sell', td))

        # Otherwise, it is a one-sided send or receive
        else:
            # TODO Move this list to a config
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
    """
    Create transaction reports based on the flatten output.

    This main loop iterates through each line in the flatten output making
    decisions about how to process each line.
    
    Lines for approvals, spam, stablecoin swaps, and equivalent swaps are 
    stored in separate lists for reference but not used in subsequent
    processing.
    
    Lines for other transactions are stored as a transaction batch and
    processed in a batch since they may need to reference each other.
    """

    txns = []
    approval_txns = []
    spam_txns = []
    stablecoin_txns = []
    equivalent_txns = []
    empty_txns = []
    
    with open(FLATTEN_OUTPUT, 'r') as f:

        headers = next(f)
        headers_list = headers.strip().split(',')
        approval_txns.append(headers_list)
        spam_txns.append(headers_list)
        stablecoin_txns.append(headers_list)
        equivalent_txns.append(headers_list)
        empty_txns.append(headers_list)

        lines = 0
        processed_lines = 0
        reader = csv.reader(f)
        txn_batch = []
        for row in reader:
            lines += 1
            txn_dict = dict(zip(FLAT_HEADERS, row))

            # Is it spam?
            # TODO Allow for a spam allowlist
            if txn_dict['spam'] == 'True':
                spam_txns.append(row)
                continue

            # Is it an approval?
            elif txn_dict['tx.name'] == 'approve':
                approval_txns.append(row)
                continue

            # Are there any ovrerrides for the token_id to use a different symbol?
            if txn_dict['sends.token_id'] in TXNS_CONFIG['token_name_overrides']:
                txn_dict['sends.token.symbol'] = \
                    TXNS_CONFIG['token_name_overrides'][txn_dict['sends.token_id']]

            if txn_dict['receives.token_id'] in TXNS_CONFIG['token_name_overrides']:
                txn_dict['receives.token.symbol'] = \
                    TXNS_CONFIG['token_name_overrides'][txn_dict['receives.token_id']]

            if txn_dict['sends.token.symbol'] == '' and \
                txn_dict['receives.token.symbol'] == '':
                empty_txns.append(row)                
                continue

            # Is it a stablecoin swap?
            if txn_dict['sends.token.symbol'].lower() in STABLECOINS and \
                    txn_dict['receives.token.symbol'].lower() in STABLECOINS:
                stablecoin_txns.append(row)
                continue

            # Is it a swap between equivalent tokens?
            if sorted([txn_dict['sends.token.symbol'].lower(), 
                txn_dict['receives.token.symbol'].lower()]) in \
                    TXNS_CONFIG['consolidated_parser']['equivalents']:
                equivalent_txns.append(row)
                continue  # Equivalents swap

            # If none of the above, then it is a transaction to be processed
            # as part of a batch (even if only a single item in batch).

            # If the sub field is not 0, then it is an ongoing part of a batch
            if txn_dict['sub'] != '0':
                txn_batch.append(txn_dict)

            # If the sub field is 0 and there is already a batch, then this
            # is a new batch and the previous batch should be processed.
            elif len(txn_batch) > 0:
                txns.extend(process_batch(txn_batch))
                txn_batch = [txn_dict]

            # If none of the others apply, then this is the first transaction.
            else:
                # First transaction
                txn_batch = [txn_dict]

            processed_lines += 1

        # This handles the last unprocessed batch
        txns.extend(process_batch(txn_batch))


    print(f'{processed_lines} / {lines}')
    return (
        txns, 
        approval_txns, 
        spam_txns, 
        stablecoin_txns, 
        equivalent_txns, 
        empty_txns
    )


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