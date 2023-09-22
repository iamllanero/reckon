import os
import tomllib

from debank import fetch_all_history
from constants import WALLETS_TOML, WALLETS_DIR

def main():
    """Build and/or refresh wallets listed in config file"""

    print(f'Building and refreshing wallets in {WALLETS_TOML}')

    with open(WALLETS_TOML, 'rb') as f:
        wf = tomllib.load(f)

    for wallet in wf['wallets']:
        id = wallet[0]
        chain_id = wallet[1]
        hl = fetch_all_history(id, chain_id)
        hl.write()

# Make sure there is a wallets_cache directory
if not os.path.isdir(WALLETS_DIR):
    print(f'Creating a wallets cache directory => {WALLETS_DIR}')
    os.makedirs(WALLETS_DIR)

if __name__ == '__main__':
    main()