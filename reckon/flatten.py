import csv
from collections import defaultdict
from debank import load_history
from config import (
    FLATTEN_OUTPUT,
    FLATTEN_PROJ_OUTPUT,
    FLATTEN_TXNAMES_OUTPUT,
    FLATTEN_RECEIVE_TOKENS_OUTPUT,
    FLATTEN_RECEIVE_TOKENS_TOML,
    FLATTEN_SEND_TOKENS_OUTPUT,
    FLATTEN_RECSEND_TOKENS_OUTPUT,
    FLATTEN_NOWALLET_OUTPUT,
    FLATTEN_DIR,
    WALLETS
)


def flatten_wallets():

    for wallet in WALLETS:
        id = wallet[0]
        chain_id = wallet[1]
        hl = load_history(id, chain_id)
        print(f'- Saving flattened {hl.get_wallet_addr()}-{hl.get_chain_id()}.csv')
        hl.write_flat_csv()


def consolidate_wallets():

    headers = False
    with open(FLATTEN_OUTPUT, 'w') as f:
        for wallet in WALLETS:
            with open(f'{FLATTEN_DIR}/{wallet[0]}-{wallet[1]}.csv', 'r') as wf:
                if headers:
                    next(wf)
                else:
                    headers = True
                for line in wf:
                    f.write(line)


def write_project_txnames():

    count_dict = defaultdict(int)
    with open(FLATTEN_OUTPUT, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            count_dict[(row['project.name'], row['tx.name'])] += 1

    # sorted_combinations = sorted(count_dict.items(), key=lambda x: x[1], reverse=True)
    sorted_combinations = sorted(count_dict.items(), key=lambda x: (x[0][0], x[0][1]))

    with open(FLATTEN_PROJ_OUTPUT, 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['project.name', 'tx.name', 'count'])
        for (project, tx), count in sorted_combinations:
            writer.writerow([project, tx, count])


def write_txnames():

    count_dict = defaultdict(int)
    with open(FLATTEN_OUTPUT, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            count_dict[row['tx.name']] += 1

    sorted_combinations = sorted(count_dict.items(), key=lambda x: (x[1]), reverse=True)

    with open(FLATTEN_TXNAMES_OUTPUT, 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['tx.name', 'count'])
        for tx, count in sorted_combinations:
            writer.writerow([tx, count])


def write_receive_tokens():

    count_dict = defaultdict(int)
    with open(FLATTEN_OUTPUT, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row['receives.token.symbol'] != '' and row['receives.token_id'] != '':
                count_dict[(
                    row['project.chain'],
                    row['receives.token.symbol'],
                    row['receives.token_id'],
                    row['receives.token.is_verified']
                )] += 1

    sorted_combinations = sorted(count_dict.items(), key=lambda x: (x[0][0], x[0][1], x[0][2], x[0][3]))

    with open(FLATTEN_RECEIVE_TOKENS_OUTPUT, 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow([
            'project.chain',
            'receives.token.symbol',
            'receives.token_id',
            'receives.token.is_verified',
            'count'
        ])
        for (
            project_chain,
            receives_token_symbol,
            receives_token_id,
            receives_token_is_verified
        ), count in sorted_combinations:
            writer.writerow([
                project_chain,
                receives_token_symbol,
                receives_token_id,
                receives_token_is_verified,
                count
            ])


def write_receive_tokens_toml():

    count_dict = defaultdict(int)
    with open(FLATTEN_OUTPUT, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row['receives.token.symbol'] != '' and row['receives.token_id'] != '':
                count_dict[(
                    row['project.chain'],
                    row['receives.token.symbol'],
                    row['receives.token_id'],
                    row['receives.token.is_verified'],
                    row['spam']
                )] += 1

    sorted_combinations = sorted(count_dict.items(), key=lambda x: (x[0][0], x[0][1], x[0][2], x[0][3], x[0][4]))

    with open(FLATTEN_RECEIVE_TOKENS_TOML, 'w', newline='') as file:
        file.write("SPAM_LIST = [\n")
        for (
            project_chain,
            receives_token_symbol,
            receives_token_id,
            receives_token_is_verified,
            spam
        ), count in sorted_combinations:
            if spam == 'True':
                file.write(f'    "{project_chain}:{receives_token_id}", # {receives_token_symbol} | {"Verified" if receives_token_is_verified == "True" else "Not Verified"} | {"Spam" if spam == "True" else "Not Spam"} | {count}\n')
        file.write("]\n\n")

        file.write("NOT_SPAM_VERIFIED_LIST = [\n")
        for (
            project_chain,
            receives_token_symbol,
            receives_token_id,
            receives_token_is_verified,
            spam
        ), count in sorted_combinations:
            if spam == 'False' and receives_token_is_verified == 'True':
                file.write(f'    "{project_chain}:{receives_token_id}", # {receives_token_symbol} | {"Verified" if receives_token_is_verified == "True" else "Not Verified"} | {"Spam" if spam == "True" else "Not Spam"} | {count}\n')
        file.write("]\n\n")

        file.write("NOT_SPAM_UNVERIFIED_NOSYMBOL_LIST = [\n")
        for (
            project_chain,
            receives_token_symbol,
            receives_token_id,
            receives_token_is_verified,
            spam
        ), count in sorted_combinations:
            if spam == 'False' and receives_token_is_verified == 'False' and receives_token_symbol == '':
                file.write(f'    "{project_chain}:{receives_token_id}", # {receives_token_symbol} | {"Verified" if receives_token_is_verified == "True" else "Not Verified"} | {"Spam" if spam == "True" else "Not Spam"} | {count}\n')
        file.write("]\n\n")

        file.write("NOT_SPAM_UNVERIFIED_LIST = [\n")
        for (
            project_chain,
            receives_token_symbol,
            receives_token_id,
            receives_token_is_verified,
            spam
        ), count in sorted_combinations:
            if spam == 'False' and receives_token_is_verified == 'False':
                file.write(f'    "{project_chain}:{receives_token_id}", # {receives_token_symbol} | {"Verified" if receives_token_is_verified == "True" else "Not Verified"} | {"Spam" if spam == "True" else "Not Spam"} | {count}\n')
        file.write("]\n")


def write_send_tokens():

    count_dict = defaultdict(int)
    with open(FLATTEN_OUTPUT, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row['sends.token.symbol'] != '' and row['sends.token_id'] != '':
                count_dict[(
                    row['project.chain'],
                    row['sends.token.symbol'],
                    row['sends.token_id'],
                    row['sends.token.is_verified']
                )] += 1

    sorted_combinations = sorted(count_dict.items(), key=lambda x: (x[0][0], x[0][1], x[0][2], x[0][3]))

    with open(FLATTEN_SEND_TOKENS_OUTPUT, 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow([
            'project.chain',
            'sends.token.symbol',
            'sends.token_id',
            'sends.token.is_verified',
            'count'
        ])
        for (
            project_chain,
            sends_token_symbol,
            sends_token_id,
            sends_token_is_verified
        ), count in sorted_combinations:
            writer.writerow([
                project_chain,
                sends_token_symbol,
                sends_token_id,
                sends_token_is_verified,
                count
            ])


def write_recsend_tokens():

    count_dict = defaultdict(int)
    with open(FLATTEN_OUTPUT, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row['receives.token.symbol'] != '' and \
            row['receives.token_id'] != '' and \
            row['sends.token.symbol'] != '' and \
            row['sends.token_id'] != '':
                count_dict[(
                    row['project.chain'],
                    row['receives.token.symbol'],
                    row['receives.token_id'],
                    row['sends.token.symbol'],
                    row['sends.token_id'],
                )] += 1

    sorted_combinations = sorted(count_dict.items(), key=lambda x: (x[0][0], x[0][1], x[0][2], x[0][3], x[0][4]))

    with open(FLATTEN_RECSEND_TOKENS_OUTPUT, 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow([
            'project.chain',
            'receives.token.symbol',
            'receives.token_id',
            'sends.token.symbol',
            'sends.token_id',
            'count'
        ])
        for (
            project_chain,
            receives_token_symbol,
            receives_token_id,
            sends_token_symbol,
            sends_token_id,
        ), count in sorted_combinations:
            writer.writerow([
                project_chain,
                receives_token_symbol,
                receives_token_id,
                sends_token_symbol,
                sends_token_id,
                count
            ])


def write_nowallet():

    # Filter the flattened file for rows with no wallet matches
    wallet_addresses = set(wallet[0].lower() for wallet in WALLETS)
    no_wallet_match_rows = []
    with open(FLATTEN_OUTPUT, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row['other_addr'].lower() not in wallet_addresses and \
               row['receives.from_addr'].lower() not in wallet_addresses and \
               row['sends.to_addr'].lower() not in wallet_addresses and \
               row['tx.from_addr'].lower() not in wallet_addresses and \
               row['tx.to_addr'].lower() not in wallet_addresses:

                no_wallet_match_rows.append(row)

    with open(FLATTEN_NOWALLET_OUTPUT, 'w', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=reader.fieldnames)
        writer.writeheader()
        for row in no_wallet_match_rows:
            writer.writerow(row)


def main():

    # Flatten the JSON from each wallet
    print('Flattening wallets from JSON to CSV')
    flatten_wallets()

    # Consolidate the flattened files to a single CSV
    print(f'Consolidating flattened files to {FLATTEN_OUTPUT}')
    consolidate_wallets()

    # Create a file with all project, txnames, and counts
    print(f'Writing project and txnames output to {FLATTEN_PROJ_OUTPUT}')
    write_project_txnames()

    # Create a file with all txnames and counts
    print(f'Writing txnames output to {FLATTEN_TXNAMES_OUTPUT}')
    write_txnames()

    # Create a file with chain, receives.token.symbol, receives.token_id, count
    print(f'Writing receive token names output to {FLATTEN_RECEIVE_TOKENS_OUTPUT}')
    write_receive_tokens()

    print(f'Writing receive token names output to {FLATTEN_RECEIVE_TOKENS_TOML}')
    write_receive_tokens_toml()

    # Create a file with chain, sends.token.symbol, sends.token_id, count
    print(f'Writing send token names output to {FLATTEN_SEND_TOKENS_OUTPUT}')
    write_send_tokens()

    # Create a file with chain, sends.token.symbol, sends.token_id, receives.token.symbol, receives.token_id, count
    print(f'Writing receive/send token pairs output to {FLATTEN_RECSEND_TOKENS_OUTPUT}')
    write_recsend_tokens()

    # Create a file where no wallet matches on other_addr, receives.from_addr, sends.to_addr, tx.from_addr
    print(f'Writing non-matching wallet entries to  {FLATTEN_NOWALLET_OUTPUT}')
    # Print out all wallet addresses
    # print('Wallet addresses:')
    # for wallet in WALLETS:
    #     print(f'- {wallet[0]}')
    write_nowallet()


if __name__ == '__main__':
    main()
