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

# Directory for flattened wallet output
FLATTEN_DIR = 'output/flatten'

if not os.path.isdir(FLATTEN_DIR):
    print(f'Creating {WALLETS_DIR}')
    os.makedirs(FLATTEN_DIR)

# File that stores the combined flattened wallet
FLATTEN_OUTPUT = 'output/flatten.csv'

# File that stores many config options for txns
TXNS_TOML = 'config/txns.toml'

with open(TXNS_TOML, 'rb') as f:
    TXNS_CONFIG = tomllib.load(f)

# Files to store key txns data
TXNS_OUTPUT = 'output/txns.csv'
SPAM_OUTPUT = 'output/txns_spam.csv'
APPROVALS_OUTPUT = 'output/txns_approvals.csv'
STABLECOINS_OUTPUT = 'output/txns_stablecoins.csv'
EQUIVALENTS_OUTPUT = 'output/txns_equivalents.csv'
EMPTY_OUTPUT = 'output/txns_empty.csv'

TAGS_FILE = 'config/tags.toml'
TAGS_LOCAL_FILE = 'config/tags_local.toml'

with open(TAGS_FILE, 'rb') as f:
    TAGS = tomllib.load(f)

    if os.path.exists(TAGS_LOCAL_FILE):
        with open(TAGS_LOCAL_FILE, 'rb') as g:
            local_tags = tomllib.load(g)

        TAGS.update(local_tags)

TRANSACTION_OVERRIDES_FILE = 'config/txoverride.toml'

if not os.path.exists(TRANSACTION_OVERRIDES_FILE):
    open(TRANSACTION_OVERRIDES_FILE, "w").write("")

with open(TRANSACTION_OVERRIDES_FILE, 'rb') as f:
    TXN_OVERRIDES = tomllib.load(f)

# File that stores the price overrides
PRICE_MANUAL_FILE = 'config/price_manual.csv'

# Key output for price.py
PRICE_OUTPUT = 'output/price.csv'
PRICE_CACHE_OUTPUT = 'output/price_cache.csv'
PRICE_MISSING_OUTPUT = 'output/price_missing.csv'

# Output of pf
PF_OUTPUT = 'output/pf.csv'

# Output of hifo8949
HIFO8949_OUTPUT = 'output/hifo8949.csv'

COINGECKO_COINS_LIST_FILE = 'data/coingecko_coins_list.json'
DEBANK_FILE = 'config/debank.toml'

# File that lists known stablecoins
STABLECOINS_TOML = 'config/stablecoins.toml'

with open(STABLECOINS_TOML, 'rb') as f:
    STABLECOINS = tomllib.load(f)['STABLECOINS']


# Dict to cache token symbols. Needed for tokens without symbols that can use
# another token (i.e. WETH) and tokens with multiple matches.
COINGECKO_ID_EXPLICIT = {
    "aave": "aave",
    "abccvx-gauge": "convex-finance",
    "abccvx": "convex-finance",
    "acrv": "aladdin-cvxcrv",
    "afrxeth": "frax-ether",
    "avax": "avalanche-2",
    "b-90clevcvx-10cvx": "convex-finance",
    "bch": "bitcoin-cash",
    "bifi": "beefy-finance",
    "bnb": "binancecoin",
    "boo": "spookyswap",
    "bshare": "based-shares",
    "clevcvx": "clever-cvx",
    "cnc": "conic-finance",
    "ctr": "concentrator",
    "cvxfxs": "convex-fxs",
    "cvxfxsfxs-f": "convex-fxs",
    "dot": "polkadot",
    "eth": "ethereum",
    "frxethcrv": "curve-dao-token",
    "ftm": "fantom",
    "geth": "geist-eth",
    "gftm": "geist-ftm",
    "gmx": "gmx",
    "grt": "the-graph",
    "ice": "ice-token",
    "ldo": "lido-dao",
    "link": "chainlink",
    "lusd": "liquity-usd",
    "memo": "wonderland",
    "mim": "magic-internet-money",
    "mootombtomb-ftm": "fantom",
    "pxcvx": "convex-finance",
    "sd": "stader",
    "sdog": "snowdog",
    "sdt": "stake-dao",
    "shib": "shiba-inu",
    "spa": "spartacus",
    "spirit-lp": "spiritswap",
    "splp": "splp",
    "sspa": "spartacus",
    "sspell": "spell-token",
    "stkcvxcrv": "convex-crv",
    "time": "wonderland",
    "tomb-v2-lp": "tomb",
    "ucrv": "curve-dao-token",
    "ucvx": "convex-finance",
    "ucvxcrv": "convex-crv",
    "usdc": "usd-coin",
    "weth": "ethereum",
    "xald": "aladdin-dao",
}

DEBANK_ALLOW_LIST = [
    "9b9854c53b5aca16cdbf5f25f9245ea5",           # veDEUS
    "0x10720a029a5e5281391be3181477e48d47d0ff91", # SDOG
    "0x8e2549225e21b1da105563d419d5689b80343e01", # sSPA
]

DEBANK_SPAM_TOKEN_IDS = [
    "0x2dbed4d7a843796c6e985db5368f2bbcaa785cda", # PEPE (FAKE VERSION)
    "0x5b942470df39cfcad4348585fb5507d4c333a91f", # BALD (FAKE VERSION)
]

DEBANK_SPAM_TOKEN_NAMES = [
    "(BNB)",
    "$ ConvexLR.com  - Visit to claim bonus rewards",
    "$ Free Claim and Play",
    "$ UniswapLR.com @ 5.75",
    "$ USDCDrop.com <- Visit to claim",
    "$ wBTCLP.com - Visit to claim bonus rewards",
    "1BNB",
    "1XBET",
    "Access token to https://dydxfi.org",
    "AIINEDIBLE",
    "AMC",
    "ARBK",
    "arbSwap.club",
    "AvaxClassic.com",
    "AWDD",
    "BABYRFD",
    "BaseX",
    "BlurAirdropBox",
    "BTCETH",
    "Claim USDC at https://chaingeusdc.top",
    "Claim USDC at https://cusdc.disusd.eth.limo",
    "CocoX",
    "CONNECT",
    "CYBER",
    "CyberX",
    "DogeX",
    "EGOD",
    "FIGHT",
    "FK12",
    "LIL",
    "LOOKSDROP.COM",
    "LPUniV3.com",
    "M32",
    "Noox Distribution Protocol",
    "NUDES",
    "PHY",
    "PNDC",
    "PPND",
    "RABBY",
    "Reward Token - Claim at https://stUSD.tech",
    "Rewards Token From https://avpool.site",
    "ROLEX",
    "RPL: Rewards Pass",
    "Socks powered by Unisocks.Fi",
    "SpaceX",
    "Swap at LINKToken.io",
    "TANK",
    "TOMI",
    "TRON",
    "Unisocks",
    "UniswapLP.com",
    "Uniswapv3LP.com",
    "USDCGOLD.COM",
    "Visit https://arbinu.fun to claim rewards.",
    "Visit https://axdom.site to claim rewards.",
    "Visit https://convex.bz to claim rewards.",
    "Visit https://creth.xyz to claim rewards.",
    "Visit https://gpepe.org to claim rewards.",
    "Visit https://gpepe.xyz to claim rewards.",
    "Visit https://incr.fi and claim genesis airdrops.",
    "Visit https://mpepe.xyz to claim rewards.",
    "Visit https://obonus.site to claim reward",
    "Visit https://usd2023.com to claim rewards",
    "Visit https://usdreward.com to claim rewards",
    "WAVAX.net",
    "WETH Powered By Noox.fi",
    "WETH Powered By Noox.Fi",
    "WETH Powered By Noox.tech",
    "X2.0",
    "X3.0",
    "YUGA x GUCCI Merch",
    "ZRO",
    "ZPR NFT",
    "ZT.WTF",
    "ZachXBT.xyz",
    "kUSDC.org",
    "mScDAIMVT",
    "mScWETHMVT",
    "moaAVXMVT",
    "wHEX",
    "NHTYWEW",
    "Incubator", # Not spam but no USD value or pricing
]