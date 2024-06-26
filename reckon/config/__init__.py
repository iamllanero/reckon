# Configuration options for Reckon
#
# Design considerations
#
# - Users should not need to directly modify this file
# - Files that need user modification should be pushed to TOML files
# - This file should validate files and dirs taking appropriate actions
#
# Some general conventions:
#
# X_TOML - Path to a TOML file
# X_OUTPUT - Path to an output file that will be overwritten
# X_DIR - Path to a directory that will be used (and created, if needed)
# X_FILE - Path to a file that will be used (and created, if needed)
# X_CONFIG - A dict that will be used as a config
# X - A variable that will be used directly (i.e. WALLETS)

import tomllib
import os
import sys

# CHECK AND MAKE OUTPUT DIRS
#############################

if not os.path.isdir('output/cache'):
    os.makedirs('output/cache')
if not os.path.isdir('output/flatten'):
    os.makedirs('output/flatten')
if not os.path.isdir('output/wallets'):
    os.makedirs('output/wallets')
if not os.path.isdir('output/work'):
    os.makedirs('output/work')
if not os.path.isdir('output/tax_hifo'):
    os.makedirs('output/tax_hifo')

###############################################################################
# GENERAL CONFIGURATION OPTIONS
###############################################################################

# File that lists known stablecoins
STABLECOINS_TOML = 'config/stablecoins.toml'

with open(STABLECOINS_TOML, 'rb') as f:
    STABLECOINS = tomllib.load(f)['STABLECOINS']

###############################################################################
# BUILD.PY CONFIGURATION OPTIONS
###############################################################################

# File that stores the wallet
WALLETS_TOML = 'config/wallets.toml'

if not os.path.isfile(WALLETS_TOML):
    sys.exit("No wallet file was found.")

with open(WALLETS_TOML, 'rb') as f:
    WALLETS = tomllib.load(f)['WALLETS']

# Directory for wallet output
WALLETS_DIR = 'output/wallets'

if not os.path.isdir(WALLETS_DIR):
    print(f'Creating {WALLETS_DIR}')
    os.makedirs(WALLETS_DIR)

DEBANK_FILE = 'config/debank.toml'
with open(DEBANK_FILE, 'rb') as f:
    debank_toml = tomllib.load(f)
    DEBANK_ALLOW_LIST = debank_toml['DEBANK_ALLOW_LIST']
    DEBANK_BLOCK_LIST = debank_toml['DEBANK_BLOCK_LIST']

###############################################################################
# FLATTEN.PY CONFIGURATION OPTIONS
###############################################################################

# Directory for flattened wallet output
FLATTEN_DIR = 'output/flatten'

if not os.path.isdir(FLATTEN_DIR):
    print(f'Creating {WALLETS_DIR}')
    os.makedirs(FLATTEN_DIR)

# File that stores the combined flattened wallet
FLATTEN_OUTPUT = 'output/flatten.csv'
FLATTEN_PROJ_OUTPUT = 'output/work/flatten_proj.csv'
FLATTEN_TXNAMES_OUTPUT = 'output/work/flatten_txnames.csv'
FLATTEN_RECEIVE_TOKENS_OUTPUT = 'output/work/flatten_receive_tokens.csv'
FLATTEN_RECEIVE_TOKENS_TOML = 'output/work/flatten_receive_tokens.toml'
FLATTEN_SEND_TOKENS_OUTPUT = 'output/work/flatten_send_tokens.csv'
FLATTEN_RECSEND_TOKENS_OUTPUT = 'output/work/flatten_recsend_tokens.csv'
FLATTEN_NOWALLET_OUTPUT = 'output/work/flatten_nowallet.csv'

###############################################################################
# TXNS.PY CONFIGURATION OPTIONS
###############################################################################

# File that stores many config options for txns
TXNS_TOML = 'config/txns.toml'
with open(TXNS_TOML, 'rb') as f:
    TXNS_CONFIG = tomllib.load(f)

# File that stores the manual txns overrides
TXNS_MANUAL_TOML = 'config/txns_manual.toml'
with open(TXNS_MANUAL_TOML, 'rb') as f:
    TXNS_MANUAL_TOML = tomllib.load(f)


# Files to store txns.py work products
TXNS_PRICE_REQ_OUTPUT = 'output/work/txns_price_req.csv'
SPAM_OUTPUT = 'output/work/txns_spam.csv'
APPROVALS_OUTPUT = 'output/work/txns_approvals.csv'
STABLECOINS_OUTPUT = 'output/work/txns_stablecoins.csv'
EQUIVALENTS_OUTPUT = 'output/work/txns_equivalents.csv'
EMPTY_OUTPUT = 'output/work/txns_empty.csv'

# Files to store key txns data
TXNS_OUTPUT = 'output/txns.csv'

# Files for tagging
TAGS_FILE = 'config/tags.toml'
TAGS_LOCAL_FILE = 'config/tags_local.toml'
with open(TAGS_FILE, 'rb') as f:
    TAGS = tomllib.load(f)

    if os.path.exists(TAGS_LOCAL_FILE):
        with open(TAGS_LOCAL_FILE, 'rb') as g:
            local_tags = tomllib.load(g)

        TAGS.update(local_tags)

###############################################################################
# PRICE.PY CONFIGURATION OPTIONS
###############################################################################

PRICE_CONFIG = 'config/price.toml'

# File that stores the price overrides
PRICE_MANUAL_FILE = 'config/price_manual.csv'

# Key output for price.py work products
PRICE_REQ_OUTPUT = 'output/work/price_req.csv'
PRICE_INFERRED_OUTPUT = 'output/work/price_inferred.csv'
PRICE_MERGED_OUTPUT = 'output/work/price_merged.csv'
PRICE_MISSING_OUTPUT = 'output/work/price_missing.csv'

# Key output for price.py main file
PRICE_OUTPUT = 'output/price.csv'

# Key output for price.py worksheet to enter manual prices needed
PRICE_WORKSHEET_OUTPUT = 'output/price_worksheet.csv'

# Key output for price.py to store the manual prices that were used
PRICE_MANUAL_USED_OUTPUT = 'output/work/price_manual_used.csv'

###############################################################################
# COINGECKO.PY CONFIGURATION OPTIONS
###############################################################################

COINGECKO_COINS_LIST_FILE = 'data/coingecko_coins_list.json'

# Dict to cache token symbols. Needed for tokens without symbols that can use
# another token (i.e. WETH) and tokens with multiple matches.
COINGECKO_TOML = 'config/coingecko.toml'
with open(COINGECKO_TOML, 'rb') as f:
    COINGECKO_ID_EXPLICIT = tomllib.load(f)['COINGECKO_ID_EXPLICIT']

# Key output for coingecko.py cache files
COINGECKO_CACHE_OUTPUT = 'output/cache/coingecko_cache.csv'
COINGECKO_MISSING_OUTPUT = 'output/cache/coingecko_missing.csv'

###############################################################################
# DEFILLAMA.PY CONFIGURATION OPTIONS
###############################################################################

# Key output for defillama.py
DEFILLAMA_CACHE_OUTPUT = 'output/cache/defillama_cache.csv'
DEFILLAMA_MISSING_OUTPUT = 'output/cache/defillama_missing.csv'

###############################################################################
# PF.PY CONFIGURATION OPTIONS
###############################################################################

# Output of pf
PF_OUTPUT = 'output/pf.csv'

###############################################################################
# TAXES_HIFO.PY CONFIGURATION OPTIONS
###############################################################################

# Output of hifo8949
TAX_HIFO_OUTPUT = 'output/tax_hifo.csv'
TAX_HIFO_DETAIL_OUTPUT = 'output/tax_hifo_detailed.csv'
TAX_HIFO_PIVOT_GAINLOSS_OUTPUT = 'output/tax_hifo_pivot_gainloss.txt'
TAX_HIFO_PIVOT_INCOME_OUTPUT = 'output/tax_hifo_pivot_income.txt'
TAX_HIFO_DIR = 'output/tax_hifo/'
TAX_HIFO_WARN_THRESHOLD = 5000
