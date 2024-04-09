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
into how calculations are performed. The overall data pipeline is as follows:

`build.py` -> `flatten.py` -> `txns.py` -> `price.py` -> `tax_hifo.py`

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
- Price generates a number of intermediate working files to help debug and
  reconcile data. One such file is `output/work/price_manual_used.csv` which
  shows a list of all of the entries in `output/price_manual.csv` that have
  been used. This can be a drop-in replacement to keep the csv file clean or
  used to do a side-by-side comparison.

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
python3 reckon/flatten.py

# Calculates taxable transactions
python3 reckon/txns.py

# Gets the pricing data
python3 reckon/price.py

# Create a close to an IRS 8949 list based on the HIFO cost basis
# WARNING: This will not run as long as there are missing prices in price.csv
python3 reckon/taxes_hifo.py
```

## HOW TO FIX DATA

Issues can typically be found by looking at the following files:

- `output/flatten.csv`
- `output/txns.csv`
- `output/price.csv`

However, Reckon also provides a lot of visibility in intermediate work files to
help make track down potential issues. Look in the `output/work` directory.

There is also a flag in the `reckon/config/__init__.py` called
TAX_HIFO_WARN_THRESHOLD that can be adjusted to help show high gain/loss values
in the console when running `tax_hifo.py`.

### Missing prices

Reckon tries to use defillama API by default and infers prices when possible.
However, if it can't figure out the price, you have a few options:

- Create price rules in `config/price.toml` to address systemic issues such as
  remapping a token symbol to another (i.e. eth to weth). Options include:
  - Changing the action to "ignore"
  - Changing the action to use "coingecko"
  - Remapping the chain, symbol, or token_id
- Create an entry in `config/price_manual.csv` to address problems in a single
  transaction. Options include:
  - Providing a manual price
  - Changing the transaction type

```csv
date,symbol,chain,token_id,timestamp,price,txn_type,comment
2021-11-29 01:03:21,fBEETS,ftm,0xfcef8a994209d6916eb2c86cdd2afd60aa6f54b1,1638147801,0.54,,debank
```

Reckon provides a handy `output/price_worksheet.csv` to use to figure out the
what's missing.

### Incorrect prices

- If a token is consistently showing the incorrect price, most likely solution
  is to create a price rule.
- If a single transaction is showing the incorrect price, look at creating a
  manual price entry in `config/price_manual.csv` in the same format as for
  missing prices.

### Showing up as income instead of a buy

- Some transactions show up incorrectly due to the way the protocol mechanism
  works. For example, a purchase that requires a subsequent claim may show up
  as income.
- Bridging is usually excluded but could also show up as income.
- The fix will likely require making an entry in `config/price_manual.csv` to
  remap the entry to a "buy" txn_type.
- An example entry is:

```csv
date,symbol,chain,token_id,timestamp,price,txn_type,comment
2023-09-28 13:08:23,FXN,eth,0x365accfca291e7d3914637abf1f7635db165bb09,1695906503,9.30,buy,0.005626406602 ETH each
```

## TODO

- Modify the flatten script to generate a file showing all tokens detected in
  the form of: chain, token_id, symbol, name, project.id, project.name, project.site_url, frequency
- Make it easy to copy items from the above list to a block list
- Modify the spam detection to use the block list instead of the current
  spam list
