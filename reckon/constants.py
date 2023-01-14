WALLETS_TOML = 'wallets.toml'
WALLETS_CACHE_DIR = 'data/wallets_cache'
CONSOLIDATED_FILE = 'data/consolidated.csv'

TXNS_TOML = 'txns.toml'
TXNS_FILE = 'data/txns.csv'
SPAM_FILE = 'data/spam.csv'
APPROVALS_FILE = 'data/approvals.csv'
TAGS_FILE = 'tags.toml'
TAGS_LOCAL_FILE = 'tags_local.toml'
PRICED_FILE = 'data/priced.csv'
PRICE_CACHE_FILE = 'data/price_cache.csv'
COINGECKO_COINS_LIST_FILE = 'data/coingecko_coins_list.json'
TRANSACTION_OVERRIDES_FILE = 'txoverride.toml'

STABLECOINS = [
    "alusd",
    "bpt-deiusdc",
    "bpt-mimusdcust",
    "bpt-guqinqi",
    "busd",
    "dai.e",
    "dai",
    "fusdt",
    "frax",
    "fraxbp-f",
    "gusd",
    "gdai",
    "hmim",
    "lusd",
    "lusd3crv-f",
    "mai",
    "mim",
    "mimatic",
    "moobeetdoubledollarfugue",
    "moobeetguqinqi2",  # Beefy Guqin Qi 2 vault
    "moogeistmim",
    "mooscreamdai",
    "s*usdc",
    "usd",
    "usdc.e",
    "usdc",
    "usde",
    "usdt",
    "usdt.e",
    "ust",
]

# Dict to cache token symbols. Needed for tokens without symbols that can use
# another token (i.e. WETH) and tokens with multiple matches.
COINGECKO_ID_EXPLICIT = {
    "aave": "aave",
    "acrv": "aladdin-cvxcrv",
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
    "cvxfxs": "frax-share",
    "cvxfxsfxs-f": "frax-share",
    "dot": "polkadot",
    "eth": "ethereum",
    "ftm": "fantom",
    "gftm": "geist-ftm",
    "geth": "geist-eth",
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
    "sspa": "spartacus",
    "splp": "splp",
    "sspell": "spell-token",
    "time": "wonderland",
    "tomb-v2-lp": "tomb",
    "ucvx": "convex-finance",
    "usdc": "usd-coin",
    "weth": "ethereum",
}

DEBANK_ALLOW_LIST = [
    "9b9854c53b5aca16cdbf5f25f9245ea5",           # veDEUS
    "0x10720a029a5e5281391be3181477e48d47d0ff91", # SDOG
    "0x8e2549225e21b1da105563d419d5689b80343e01", # sSPA
]

