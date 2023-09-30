import csv
from collections import defaultdict
from debank import load_history
from config import (
    FLATTEN_OUTPUT, 
    FLATTEN_PROJ_OUTPUT, 
    FLATTEN_TXNAMES_OUTPUT, 
    FLATTEN_DIR, 
    WALLETS
)


def flatten_wallets():

    print('Flattening wallets')

    for wallet in WALLETS:
        id = wallet[0]
        chain_id = wallet[1]
        hl = load_history(id, chain_id)
        print(f'- Saving flattened {hl.get_wallet_addr()}-{hl.get_chain_id()}.csv')
        hl.write_flat_csv()


def consolidate_wallets():

    print(f'Consolidating flattened files to {FLATTEN_OUTPUT}')

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


def create_project_txnames():

    print(f'Writing project and txnames output to {FLATTEN_PROJ_OUTPUT}')

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


def create_txnames():

    print(f'Writing txnames output to {FLATTEN_TXNAMES_OUTPUT}')

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


def main():

    flatten_wallets()
    consolidate_wallets()
    create_project_txnames()
    create_txnames()


if __name__ == '__main__':
    main()