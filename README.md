# Reckon

- Author: Llanero
- Twitter: @iamllanero

## WARNING

This is not ready for prime time yet! Although this project does not do
anything destructive on the blockchain, it does consume Debank credits and
uses the CoinGecko API.

Use at your own peril.

## DESCRIPTION

Reckon is a series of Python scripts to perform various calculations on
cryptocurrency. Rather than a monolithich app, I've opted to keep it as
a series of different scripts for now.

Here are the main scripts (in order of intended use):

`build.py`

- Responsible for obtaining onchain wallet data
- Uses `wallets.toml` for wallet addresses
- Depends on `constants.py` and `utils.py`
- Depends on `debank.py` for working with the API and object model
- Builds and refreshes wallets using Debank API (and debank.py)
- Stores data as JSON files for each wallet

`flatten.py`

- Creates CSV versions of wallet JSON files
= Consolidates to `consolidated.csv`
- Uses `wallets.toml` for wallet addresses
- Uses `tags.toml` for address tagging
- Depends on `constants.py` and `utils.py`
- Depends on `debank.py` for working with the API and object model
- Creates a denormalized CSV of the JSON wallets
- Augments with spam detection, address tags, and transaction URLs

`txns.py`

- Responsible for compilling meaningful transactions from:
  - The `wallets.py` `consolidated.csv` output
  - Reports from coinbase, binance, blockfi
  - Manual reports
- Output is a single `txns.csv` file of all transactions
- Uses `txns.toml` to get reports and some configuration options
- Depends on `constants.py` and `utils.py`

`price.py`

- Responsible for adding USD value to transactions from `txns.csv` through a
  combination of inference, CoinGecko API, and caching
- Output is `priced.csv` which adds an additional column, 'usd_value'
- Uses `price_cache.csv` as a cache for pricing data and manually entered
  price information.
- Depends on `coingecko.py` to handle all API calls and caching
- Requires manual maintenance of the `coingecko_coins_list.json`

`8949-hifo.py`

- Responsible for generating a IRS 8949-like report that shows the following
  columns:
  - Symbol
  - Date acquired
  - Date sold
  - Proceeds
  - Cost basis
  - Gain or loss
- Uses the HIFO (highest in, first out) strategy which will take the least
  gains (or highest losses)

`pf.py`

- Creates `py.csv` a view portfolio style view that shows for every token:
  - Name
  - Current Qty
  - Gain Loss
  - Unit Cost
  - Buy Qty
  - Buy USD
  - Buy Unit Price
  - Sell Qty
  - Sell USD
  - Sell Unit Price
  - Income Qty
  - Income USD
  
## HIFO Algorithm

- Sort dataframe (df) by date
- Go through row by row, when hit a sell transaction:
  - Scan backward to the highest not fully sold (qty-qty_sold > 0) transaction
  - Compute how much of the qty to sell and enter amount into qty_sold
  - If all sold is accounted for, stop; else repeat with scan

## SETUP

You will need an access key and credits from Debank Cloud. You can get them
at <https://cloud.debank.com/>.

Be sure to configure the following files in the config directory:

- `wallets.toml` (see `wallets_sample.toml`)
- `debank.toml`
- `txns.toml` - reports from CEX and trade equivalents

Other files with configuration type items that don't need to be changed:

- `tags.toml` - list of address tags
- `constants.py` - file locations, stablecoins
- `data/price_cache.csv` - price cache and also manual entries

Consider getting an updated version of the `coingecko_coins_list.json` from
<https://www.coingecko.com/en/api/documentation> under /coins/list. You can just
click on "Try it out" and cut/paste the resulting content to replace the current
`coingecko_coins_list.json`.

## USAGE

```sh
# Be sure you have set DEBANK_ACCESSKEY in your environment
export DEBANK_ACCESSKEY="mykey"

# First build the local cache of wallets.
# Be aware that this script uses Debank credits. It does cache aggressively
# to conserve credits. Run this script any time your wallets will have onchain
# transactions that are not yet cached. This script, via the debank module, 
# is responsible for flagging likely spam transactions.

python3 reckon/build.py

# Flatten the wallets into CSV files and consolidates into a single file.

python3 reckon/flat.py

# Calculates taxable transactions based on flatten output, generating a
# transactions file txns.csv from wallets and CEX reports into a single. Also
# generates a number of additional txns_xyz.csv files to show processing
# results.

python3 reckon/txns.py

# Fill in the gaps for prices using the CoinGecko API and any manually 
# entered prices in the "price_cache.csv" file creating a new file "priced.csv"

python3 reckon/price.py

# WIP
# Create a close to an IRS 8949 list based on the HIFO cost basis

python3 reckon/8949-hifo.py
```

