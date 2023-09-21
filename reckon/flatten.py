import tomllib

from debank import load_history
from constants import WALLETS_TOML, CONSOLIDATED_FILE, WALLETS_CACHE_DIR

def main():

    print(f'Flattening wallets in {WALLETS_TOML}')

    with open(WALLETS_TOML, 'rb') as f:
        wf = tomllib.load(f)

    for wallet in wf['wallets']:
        id = wallet[0]
        chain_id = wallet[1]
        hl = load_history(id, chain_id)
        print(f'Saving flattened {hl.get_wallet_addr()}-{hl.get_chain_id()}.csv')
        hl.write_flat_csv()

    # Consolidate flattened wallets
    print(f'Consolidating files to {CONSOLIDATED_FILE}')
    headers = False
    with open(CONSOLIDATED_FILE, 'w') as f:
        for wallet in wf['wallets']:
            with open(f'{WALLETS_CACHE_DIR}/{wallet[0]}-{wallet[1]}.csv', 'r') as wf:
                if headers:
                    next(wf)
                else:
                    headers = True
                for line in wf:
                    f.write(line)


if __name__ == '__main__':
    main()