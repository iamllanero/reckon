import sys
import os
import tomllib

from reckon.debank import *
from reckon.constants import WALLETS_TOML, CONSOLIDATED_FILE, WALLETS_CACHE_DIR

def cmd_build():
    """Build and/or refresh wallets listed in config file"""

    print(f'Building and refreshing wallets in {WALLETS_TOML}')

    with open(WALLETS_TOML, 'rb') as f:
        wf = tomllib.load(f)

    for wallet in wf['wallets']:
        id = wallet[0]
        chain_id = wallet[1]
        hl = fetch_all_history(id, chain_id)
        hl.write()


def cmd_flatten():

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


# Make sure there is a wallets_cache directory
if not os.path.isdir(WALLETS_CACHE_DIR):
    print(f'Creating a wallets cache directory => {WALLETS_CACHE_DIR}')
    os.makedirs(WALLETS_CACHE_DIR)

if __name__ == '__main__':

    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        if cmd == 'build':
            cmd_build()
        elif cmd == 'flatten':
            cmd_flatten()
    else:
        print("""
Usage:
    build        Builds or refreshes all wallets
    flatten      Creates a flattened CSV of all wallets
    """)
