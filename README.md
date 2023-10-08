# Reckon

- Author: Llanero
- Twitter: @iamllanero

## WARNING

This is not ready for prime time yet! Although this project does not do
anything destructive on the blockchain, it does consume Debank credits and
uses the DefiLlama and CoinGecko API.

Use at your own peril.

## DESCRIPTION

Reckon is a series of Python scripts to perform various calculations on
cryptocurrency. Rather than one monolithic app, reckon uses a series of
different, focused scripts with intermediate outputs to provide transparency
into how calculations are performed.

Here are the main scripts (in order of intended use):

`build.py`

- Responsible for obtaining onchain wallet data
- Uses `config/wallets.toml` for wallet addresses
- Depends on `debank` module for working with the API and object model
- Builds and refreshes wallets using Debank API
- Stores data as JSON files for each wallet in the `output/wallets` dir

`flatten.py`

- Creates a denormalized CSV of the JSON wallets in the `output/flatten` dir
- Augments data with spam detection, address tags, and transaction URLs
- Consolidates to `output/flatten.csv`
- Provides a number of work outputs in `output/work`
- Uses `config/wallets.toml` for wallet addresses
- Uses `config/tags.toml` for address tagging
- Depends on `debank` module for working with the API and object model

`txns.py`

- Responsible for compilling meaningful transactions from:
  - `output/flatten.csv`
  - Reports as listed in `config/txns.toml`
- Output is a single `txns.csv` file of all transactions
- Uses `config/txns.toml` to get reports and some configuration options

`price.py`

- Responsible for adding USD value to transactions from `txns.csv` through a
  combination of DefiLlama, CoinGecko API, inference, and overrides.
- Uses `config/price.toml` to determine pricing rules.
- Uses `config/price_manual.csv` allowing final overrides. Note that the price
  column should be UNIT price (not total USD value).
- Output is `output/price.csv` and `output/price_worksheet.csv` if there are
  any missing prices
- Price rules defaults to defillama, but uses coingecko for non-EVM chains
  as well as problematic tokens. Refer to `config/price.toml` for more info
  on configuring the price rules.
- Depends on `defillama` and `coingecko` modules to handle API calls and
  caching.

`tax_hifo.py`

- Responsible for generating data for IRS 8949-like reporting
- Uses the HIFO (highest in, first out) strategy which will take the least
  gains (or highest losses)
- Output is a combination of the following:
  - `output/tax_hifo.csv` that provides capital gains and income on a per-year,
    per-token basis
  - `output/tax_hifo_pivot_gainloss.txt` that contains a summary table of
    capital gains and losses
  - `output/tax_hifo_pivot_income.txt` that contains a summary table of
    all income transactions
  - `output/tax_hifo/` contains detailed reporting for every taxable token

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
  

## SETUP

You will need an access key and credits from Debank Cloud. You can get them
at <https://cloud.debank.com/>.

Be sure to configure the following file in the config directory:

- `config/wallets.toml` (see `wallets_sample.toml`)

Other files with configuration type items that don't need to be changed:

- `config/coingecko.toml`
- `config/debank.toml`
- `config/stablecoins.toml`
- `config/tags.toml` - list of address tags
- `config/txns.toml` - reports from CEX and trade equivalents

Consider getting an updated version of the `coingecko_coins_list.json` from
<https://www.coingecko.com/en/api/documentation> under /coins/list. You can just
click on "Try it out" and cut/paste the resulting content to replace the current
`data/coingecko_coins_list.json`.

## USAGE

```sh
# Be sure you have set DEBANK_ACCESSKEY in your environment
export DEBANK_ACCESSKEY="mykey"

# First build the local cache of wallets.
python3 reckon/build.py

# Flatten the wallets into CSV files and consolidates into a single file.
python3 reckon/flat.py

# Calculates taxable transactions
python3 reckon/txns.py

# Gets the pricing data
python3 reckon/price.py

# Create a close to an IRS 8949 list based on the HIFO cost basis
python3 reckon/taxes_hifo.py
```

