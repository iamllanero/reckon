WALLETS_TOML = 'config/wallets.toml'
WALLETS_CACHE_DIR = 'data/wallets_cache'
CONSOLIDATED_FILE = 'data/consolidated.csv'

TXNS_TOML = 'config/txns.toml'
TXNS_FILE = 'data/txns.csv'
SPAM_FILE = 'data/spam.csv'
APPROVALS_FILE = 'data/approvals.csv'
TAGS_FILE = 'config/tags.toml'
TAGS_LOCAL_FILE = 'config/tags_local.toml'
PRICED_FILE = 'data/priced.csv'
PRICE_CACHE_FILE = 'data/price_cache.csv'
PRICE_MANUAL_FILE = 'data/price_manual.csv'
PRICE_MISSING_FILE = 'data/price_missing.csv'
COINGECKO_COINS_LIST_FILE = 'data/coingecko_coins_list.json'
TRANSACTION_OVERRIDES_FILE = 'config/txoverride.toml'
DEBANK_FILE = 'config/debank.toml'

STABLECOINS = [
    "alusd",
    "bpt-deiusdc",
    "bpt-guqinqi",
    "bpt-mimusdcust",
    "busd",
    "cad"
    "clevusd",
    "clevusd3crv-f",
    "crvusd",
    "crvusdusdc-f",
    "dai.e",
    "dai",
    "frax",
    "fraxbp-f",
    "fusdt",
    "gdai",
    "gusd",
    "hmim",
    "lusd",
    "lusd3crv-f",
    "mai",
    "mim",
    "mimatic",
    "moobeetdoubledollarfugue",
    "moobeetguqinqi2",
    "moogeistmim",
    "mooscreamdai",
    "s*usdc",
    "usd",
    "usdc.e",
    "usdc",
    "usde",
    "usdt.e",
    "usdt",
    "ust",
]

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