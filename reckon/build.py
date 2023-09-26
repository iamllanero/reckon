from debank import fetch_all_history
from config import WALLETS

def main():
    """Build and/or refresh wallets listed in config file"""

    for wallet in WALLETS:
        id = wallet[0]
        chain_id = wallet[1]
        hl = fetch_all_history(id, chain_id)
        hl.write()

if __name__ == '__main__':
    main()