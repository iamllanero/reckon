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
    TXNS_MANUAL_TOML,
    TXNS_CONFIG,
    TAGS,
)
from debank import FLAT_HEADERS
# from utils import list_to_csv

HEADERS = [
    'date',
    'txn_type',
    'qty',
    'symbol',
    'token_id',
    'purchase_token_cost',
    'purchase_token',
    'purchase_token_id',
    'chain',
    'project',
    'txn_name',
    'wallet',
    'id',
]


def parse_report(fn, parser):
    if not os.path.isfile(fn):
        print(f'WARN: {fn} from {TXNS_TOML} not found')
        return []

    module = importlib.import_module(f'txn_parser.{parser}')
    method = getattr(module, "parse")
    return method(fn)

# TODO Change report processing to use tx_line (and maybe externalize)


def sort_except(list, ignore):
    temp = list.pop(ignore)
    list.sort(key=lambda x: datetime.datetime.strptime(
        x[0], '%Y-%m-%d %H:%M:%S'))
    list.insert(ignore, temp)


def write_csv(list, file_path):
    with open(file_path, 'w', newline='') as csvfile:
        csvwriter = csv.writer(csvfile)
        csvwriter.writerows(list)


def create_price_requests(txns):
    """
    Create a CSV file of price requests for tokens that need to be priced.
    """

    requests = [[
        'date',
        'chain',
        'qty',
        'symbol',
        'token_id',
        'txn_type',
        'purchase_token_cost',
        'purchase_token',
        'purchase_token_id',
    ]]
    for txn in txns:
        txn_dict = dict(zip(HEADERS, txn))
        if txn_dict['txn_type'] in ['buy', 'sell', 'income'] and \
                txn_dict['symbol'].lower() not in STABLECOINS and \
                txn_dict['purchase_token'].lower() not in STABLECOINS:
            requests.append([
                txn_dict['date'],
                txn_dict['chain'],
                txn_dict['qty'],
                txn_dict['symbol'],
                txn_dict['token_id'],
                txn_dict['txn_type'],
                txn_dict['purchase_token_cost'],
                txn_dict['purchase_token'],
                txn_dict['purchase_token_id'],
            ])
    print(f"Created {len(requests)} price requests")
    write_csv(requests, TXNS_PRICE_REQ_OUTPUT)


def txline(txn_type, txn_dict):
    show_tags = TXNS_CONFIG['output'].get("show_tags", False)

    date = datetime.datetime.utcfromtimestamp(
        float(txn_dict['time_at'])).strftime('%Y-%m-%d %H:%M:%S')
    # print(f"txn_dict=>{txn_dict}")
    line = [
        date,
        txn_type,
        txn_dict['receives.amount'],
        txn_dict['receives.token.symbol'],
        txn_dict['receives.token_id'] if 'receives.token_id' in txn_dict else '',
        txn_dict['sends.amount'],
        txn_dict['sends.token.symbol'],
        txn_dict['sends.token_id'] if 'sends.token_id' in txn_dict else '',
        txn_dict['project.chain'],
        txn_dict['project.name'],
        txn_dict['tx.name'],
        txn_dict['tx.from_addr'] if not show_tags else
        TAGS.get(txn_dict['tx.from_addr'], txn_dict['tx.from_addr']),
        txn_dict['id'],
    ]
    return line


def process_batch(txn_dicts, do_overrides=True):
    """
    Process a transaction batch, creating sell and buy transactions as needed.

    This function contains the main logic for categorizing transactions as
    buys, sells, income, etc. It assumes pre-processing has been done in the
    consolidated_txns() function to remove spam, approvals, etc.
    """

    txns = []

    # If transaction id has an override entry, generate lines directly from it
    if txn_dicts[0]['id'] in TXNS_MANUAL_TOML.keys():
        manuals = TXNS_MANUAL_TOML[txn_dicts[0]['id']]
        # If manuals is an emtpy dict, then ignore the txn altogether
        if not manuals == [{}]:
            # Otherwise, generate lines from the manual entry
            print(f"WARN: Manual override {txn_dicts[0]['id']}")
            for txline_data in TXNS_MANUAL_TOML[txn_dicts[0]['id']]:
                tl = []
                for header in HEADERS:
                    tl.append(txline_data[header])
                txns.append(tl)
        else:
            print(f"WARN: Skipping {txn_dicts[0]['id']} due to empty manual override")
        return txns

    # If multi-line txn, use average to calculate deposit and withdrawals
    if len(txn_dicts) > 1:

        send_amounts = [float(i['sends.amount']) if i['sends.amount'] else 0.0
                        for i in txn_dicts]
        recv_amounts = [float(i['receives.amount']) if i['receives.amount'] else 0.0
                        for i in txn_dicts]

        nonzero_sends = sum([1 for i in send_amounts if i > 0])
        nonzero_recvs = sum([1 for i in recv_amounts if i > 0])

        # TODO Need to add token_id to this logic!!!
        if nonzero_sends == 1 and nonzero_recvs == len(txn_dicts):
            # One token was sent, multiple were received back
            for td in txn_dicts:
                td['sends.token.symbol'] = txn_dicts[0]['sends.token.symbol']
                td['sends.token_id'] = txn_dicts[0]['sends.token_id']
                td['sends.amount'] = sum(
                    send_amounts) / float(len(send_amounts))

        if nonzero_recvs == 1 and nonzero_sends == len(txn_dicts):
            # Multiple tokens were sent, one was received back
            for td in txn_dicts:
                td['receives.token.symbol'] = txn_dicts[0]['receives.token.symbol']
                td['receives.token_id'] = txn_dicts[0]['receives.token_id']
                td['receives.amount'] = sum(
                    recv_amounts) / float(len(recv_amounts))

    # Generate transaction line(s) for each transaction in batch
    for td in txn_dicts:

        # print(f"td=> {td}")
        sends_token = td['sends.token.symbol'].lower()
        receives_token = td['receives.token.symbol'].lower()

        # If both are filled, must be a swap of some kind.
        # Unless one side is a stablecoin, this means both a buy and sell transaction
        if sends_token != '' and receives_token != '':

            # If not selling to stables, include "buy" transaction
            if receives_token not in STABLECOINS:
                txns.append(txline('buy', td))

            # If not buying w/stables, include "sell" transaction
            if sends_token not in STABLECOINS:

                # Swap sends and receives for sell transaction
                td['receives.amount'], td['sends.amount'] = \
                    td['sends.amount'], td['receives.amount']
                td['receives.token.symbol'], td['sends.token.symbol'] = \
                    td['sends.token.symbol'], td['receives.token.symbol']
                td['receives.token_id'], td['sends.token_id'] = \
                    td['sends.token_id'], td['receives.token_id']

                txns.append(txline('sell', td))

        else:
            # Otherwise, it is income or a one-sided send or receive

            # If tx.name is in the income_txns list, it is income
            if receives_token != '' and td['tx.name'] in TXNS_CONFIG['income_txns']:
                txns.append(txline('income', td))

            # If receive token is present, assume it is a receive
            elif receives_token != '':
                txns.append(txline('receive', td))

            # Everything else is a send
            else:
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

    print(f"Processing {FLATTEN_OUTPUT}")

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
            if txn_dict['spam'] == 'True':
                spam_txns.append(row)
                continue

            # Is it an approval?
            elif txn_dict['tx.name'] == 'approve':
                approval_txns.append(row)
                continue

            # Is it an empty transaction?
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

    print(f"- Lines: {lines}")
    print(f"- Processed: {processed_lines}")
    return (
        txns,
        approval_txns,
        spam_txns,
        stablecoin_txns,
        equivalent_txns,
        empty_txns
    )


def main():

    # Create list of transactions with headers
    txns = [HEADERS]

    # Get all of the transactions from the flatten output
    (consolidated,
     approval_txns,
     spam_txns,
     stable_txns,
     equivalent_txns,
     empty_txns) = consolidated_txns()

    # Add to the list of transactions
    txns.extend(consolidated)

    # Add reports to the list of transactions
    print("Processing reports")
    reports = TXNS_CONFIG['reports']
    for key in reports.keys():
        no_lines = len(txns)
        txns.extend(
            parse_report(
                reports[key]['file'],
                reports[key]['parser'],
            )
        )
        print(f'- {reports[key]["file"]} => Added {len(txns) - no_lines} entries')

    # Sort output data for easier reading
    sort_except(txns, 0)

    print(f"Created {len(txns)} transactions")

    # Write a bunch of work files to help with debugging
    write_csv(txns, TXNS_OUTPUT)
    write_csv(approval_txns, APPROVALS_OUTPUT)
    write_csv(spam_txns, SPAM_OUTPUT)
    write_csv(stable_txns, STABLECOINS_OUTPUT)
    write_csv(equivalent_txns, EQUIVALENTS_OUTPUT)
    write_csv(empty_txns, EMPTY_OUTPUT)

    # Create a list of txns that need prices
    create_price_requests(txns)


if __name__ == '__main__':

    # if len(sys.argv) > 1:
    #     cmd = sys.argv[1]
    #     if cmd == 'init_override':
    #         cmd_init_override(sys.argv[2:])
    # else:
    #     main()

    main()
