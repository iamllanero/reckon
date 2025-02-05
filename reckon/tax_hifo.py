from config import (
    PRICE_OUTPUT,
    TAX_HIFO_OUTPUT,
    TAX_HIFO_DETAIL_OUTPUT,
    TAX_HIFO_PIVOT_GAINLOSS_OUTPUT,
    TAX_HIFO_PIVOT_INCOME_OUTPUT,
    TAX_HIFO_DIR,
    TAX_HIFO_WARN_THRESHOLD,
)
from datetime import datetime
import csv
import re
from typing import List, Dict, Any, Tuple


def init_files() -> None:
    """Initialize output files with headers."""
    with open(TAX_HIFO_DETAIL_OUTPUT, 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow([
            'symbol',
            'buy_date',
            'sell_date',
            'qty',
            'cost_basis',
            'proceeds',
            'gain_loss',
            'duration_held',
            'sell_year',
            'st_lt',
            'buy_chain',
            'buy_id',
            'sell_chain',
            'sell_id',
        ])


def get_transactions() -> List[Dict[str, Any]]:
    """
    Read and parse transactions from CSV, converting data types at the source.
    Returns list of transactions with parsed dates and numbers.
    """
    with open(PRICE_OUTPUT, 'r') as file:
        reader = csv.DictReader(file)
        transactions = []
        for row in reader:
            transactions.append({
                'date': datetime.strptime(row['date'], '%Y-%m-%d %H:%M:%S'),
                'qty': float(row['qty']),
                'usd_value': float(row['usd_value']),
                'symbol': row['symbol'],  # Keep original symbol for display
                'symbol_normalized': row['symbol'].lower(),  # Add normalized version for comparisons
                'txn_type': row['txn_type'],
                'chain': row['chain'],
                'id': row['id'],
                'token_id': row['token_id']
            })
        return transactions


def validate_remaining_transactions(buys: List[Dict[str, Any]]) -> None:
    """Validate that remaining transactions have positive quantities."""
    for buy in buys:
        if buy['qty'] <= 0:
            print(f"WARNING: Found remaining transaction with non-positive quantity: {buy}")


def calculate_buy_sell_pairs(transactions: List[Dict[str, Any]], target_symbol: str) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Calculate buy/sell pairs using HIFO method."""
    # Debug: Print total quantities
    total_buy_qty = sum(txn['qty'] for txn in transactions
                       if txn['txn_type'] in ['buy', 'income']
                       and txn['symbol_normalized'] == target_symbol.lower())
    total_sell_qty = sum(txn['qty'] for txn in transactions
                        if txn['txn_type'] == 'sell'
                        and txn['symbol_normalized'] == target_symbol.lower())
    print(f"Debug: {target_symbol} - Total Buy Qty: {total_buy_qty}, Total Sell Qty: {total_sell_qty}")

    # Filter transactions by the target symbol
    buys = [
        txn for txn in transactions
        if txn['txn_type'] in ['buy', 'income']
        and txn['symbol_normalized'] == target_symbol.lower()
    ]

    sells = [
        txn for txn in transactions
        if txn['txn_type'] == 'sell'
        and txn['symbol_normalized'] == target_symbol.lower()
    ]

    # Sort buys/incomes by unit value in descending order (HIFO)
    buys.sort(key=lambda x: x['usd_value'] / x['qty'], reverse=True)

    buy_sell_pairs = []

    for sell in sells:
        sell_qty = sell['qty']
        sell_unit_price = sell['usd_value'] / sell['qty']
        sell_date = sell['date']

        # Filter out buys/incomes that happened after the sell date
        valid_buys = [buy for buy in buys if buy['date'] <= sell['date']]

        while sell_qty > 0 and valid_buys:
            buy = valid_buys[0]
            buy_qty_available = buy['qty']
            buy_unit_price = buy['usd_value'] / buy['qty']
            buy_date = buy['date']

            # Sell as much as possible from the buy transaction
            sold_qty = min(buy_qty_available, sell_qty)
            gain_loss = (sold_qty * sell_unit_price) - (sold_qty * buy_unit_price)
            duration_held = (sell_date - buy_date).days

            buy_sell_pairs.append({
                'buy_date': buy_date,
                'sell_date': sell_date,
                'qty': sold_qty,
                'cost_basis': sold_qty * buy_unit_price,
                'proceeds': sold_qty * sell_unit_price,
                'gain_loss': gain_loss,
                'duration_held': duration_held,
                'buy_chain': buy['chain'],
                'buy_id': buy['id'],
                'sell_chain': sell['chain'],
                'sell_id': sell['id'],
            })

            if gain_loss > TAX_HIFO_WARN_THRESHOLD:
                print(f"WARN: Gain/loss of {gain_loss:,.2f} for {sold_qty:.4f} {target_symbol} sold on {sell_date} after {duration_held} days")

            if buy_qty_available <= sell_qty:
                index_to_remove = buys.index(buy)
                buys.pop(index_to_remove)
                valid_buys.pop(0)
            else:
                index_to_update = buys.index(buy)
                buys[index_to_update]['qty'] = buy_qty_available - sold_qty
                buys[index_to_update]['usd_value'] = (buy_qty_available - sold_qty) * buy_unit_price

            sell_qty -= sold_qty

    validate_remaining_transactions(buys)

    # Remaining unsold assets
    unsold_assets = [{
        'buy_date': buy['date'],
        'buy_qty': buy['qty'],
        'usd_value': buy['usd_value']
    } for buy in buys if buy['qty'] > 0]

    return buy_sell_pairs, unsold_assets


def determine_qty_remaining(transactions: List[Dict[str, Any]], target_symbol: str) -> Tuple[float, float]:
    """Calculate remaining quantity for a given symbol."""
    transactions = [txn for txn in transactions if txn['symbol_normalized'] == target_symbol.lower()]

    buy_qty = sum(txn['qty'] for txn in transactions if txn['txn_type'] in ['buy', 'income'])
    sell_qty = sum(txn['qty'] for txn in transactions if txn['txn_type'] == 'sell')

    return buy_qty, sell_qty


def aggregate_results_by_year(buy_sell_pairs: List[Dict[str, Any]]) -> Dict[int, Dict[str, float]]:
    """Aggregate results by year."""
    yearly_data = {}

    for result in buy_sell_pairs:
        year = result['sell_date'].year
        if year not in yearly_data:
            yearly_data[year] = {
                'qty_sold': 0,
                'total_gain_loss': 0
            }
        yearly_data[year]['qty_sold'] += result['qty']
        yearly_data[year]['total_gain_loss'] += result['gain_loss']

    return yearly_data


def find_symbols(transactions: List[Dict[str, Any]]) -> Tuple[List[str], Dict[str, List[str]]]:
    """Find all symbols and identify duplicates."""
    symbol_to_token_id = {}
    duplicates = {}
    symbols = set()

    for txn in transactions:
        symbol = txn['symbol']  # Use original symbol format
        token_id = txn['token_id']
        symbols.add(symbol)
        if symbol in symbol_to_token_id:
            if token_id not in symbol_to_token_id[symbol]:
                symbol_to_token_id[symbol].append(token_id)
                duplicates[symbol] = symbol_to_token_id[symbol]
        else:
            symbol_to_token_id[symbol] = [token_id]

    return sorted(symbols), duplicates


def make_filename_safe(s: str, max_length: int = 255) -> str:
    """Make a string safe for use as a filename."""
    s = re.sub(r'[<>:"/\\|?*]', '_', s)
    s = re.sub(r'[\0-\31]', '', s)
    s = s.replace('..', '_')
    return s[:max_length]


def create_report(symbol: str, buy_sell_pairs: List[Dict[str, Any]], unsold_assets: List[Dict[str, Any]], incomes: List[Dict[str, Any]]) -> None:
    """Create a detailed report for a symbol."""
    if not buy_sell_pairs and not unsold_assets and not incomes:
        print(f"No report for {symbol}")
        return

    with open(f'{TAX_HIFO_DIR}/{make_filename_safe(symbol)}.txt', 'w') as file:
        print(f"Creating report for {symbol}")
        file.write(f"Tax HIFO Report for {symbol}\n\n")
        remaining_qty = sum(float(asset['buy_qty']) for asset in unsold_assets)
        file.write(f"Remaining {symbol}: {remaining_qty:,.8f}\n")
        if remaining_qty > 0:
            avg_unit_cost = sum(float(asset['usd_value']) for asset in unsold_assets) / remaining_qty
            file.write(f"Avg Unit Cost: ${avg_unit_cost:,.2f}\n")

        years = {pair['sell_date'].year for pair in buy_sell_pairs}
        years.update({income['date'].year for income in incomes})

        for year in sorted(years):
            yearly_buy_pairs = [pair for pair in buy_sell_pairs if pair['sell_date'].year == year]
            yearly_incomes = [income for income in incomes if income['date'].year == year]

            file.write("-" * 92 + "\n")
            file.write(f"Year {year}\n")
            file.write("-" * 92 + "\n")

            file.write(f"Number of Transactions: {len(yearly_buy_pairs)}\n")
            file.write(f"Quantity Sold: {sum(pair['qty'] for pair in yearly_buy_pairs):,.8f}\n")
            file.write(f"Capital Gains/Loss: ${sum(pair['gain_loss'] for pair in yearly_buy_pairs):,.2f}\n")
            file.write(f"Total Income: ${sum(income['usd_value'] for income in yearly_incomes):,.2f}\n")

            if yearly_buy_pairs:
                file.write("\nBuy/Sell Pairs\n")
                file.write("Buy Date    Sell Date   Qty             Cost Basis      Proceeds        Gain/Loss       Held\n")
                file.write("----------  ----------  --------------  --------------  --------------  --------------  ----\n")
                for pair in yearly_buy_pairs:
                    file.write(f"{pair['buy_date'].strftime('%Y-%m-%d')}  ")
                    file.write(f"{pair['sell_date'].strftime('%Y-%m-%d')}  ")
                    file.write(f"{pair['qty']:14,.8f}  ")
                    file.write(f"{pair['cost_basis']:14,.2f}  ")
                    file.write(f"{pair['proceeds']:14,.2f}  ")
                    file.write(f"{pair['gain_loss']:14,.2f}  ")
                    file.write(f"{int(pair['duration_held']):>4}\n")

            if yearly_incomes:
                file.write("\nIncome\n")
                file.write("Date        Qty             USD Value\n")
                file.write("----------  --------------  --------------\n")
                for income in yearly_incomes:
                    file.write(f"{income['date'].strftime('%Y-%m-%d')}  ")
                    file.write(f"{income['qty']:14,.8f}  ")
                    file.write(f"{income['usd_value']:14,.4f}\n")

            file.write("\n")

        if unsold_assets:
            file.write("\nRemaining (Unsold) Assets\n")
            file.write("Buy Date    Qty             USD Cost        Unit Cost\n")
            file.write("----------  --------------  --------------  ------------\n")
            for asset in unsold_assets:
                unit_cost = float(asset['usd_value']) / float(asset['buy_qty'])
                file.write(f"{asset['buy_date'].strftime('%Y-%m-%d')}  ")
                file.write(f"{float(asset['buy_qty']):14,.8f}  ")
                file.write(f"{float(asset['usd_value']):14,.2f}  ")
                file.write(f"{unit_cost:12,.2f}\n")

        file.write(f"\n\nGenerated at {datetime.now()}\n")


def pivot_table(col: str, row: str, value: str, lines: List[List[Any]]) -> Dict[str, Dict[str, float]]:
    """Create a pivot table from the data."""
    pivot_data = {}
    header = lines[0]
    for line in lines[1:]:
        col_data = str(line[header.index(col)])
        row_data = str(line[header.index(row)])
        value_data = float(line[header.index(value)])
        if col_data not in pivot_data:
            pivot_data[col_data] = {}
        if row_data not in pivot_data[col_data]:
            pivot_data[col_data][row_data] = 0
        pivot_data[col_data][row_data] = value_data
    return pivot_data


def write_pivot(pivot_data: Dict[str, Dict[str, float]], file_path: str) -> None:
    """Write a pivot table to a file."""
    with open(file_path, 'w') as f:
        f.write("Tax HIFO Pivot Table\n\n")

        unique_rows = set()
        for row_data in pivot_data.values():
            unique_rows.update(row_data.keys())
        unique_rows = sorted(list(unique_rows), key=str.lower)

        col_totals = {col: sum(row_data.values()) for col, row_data in pivot_data.items()}

        f.write(f"{'':25}")
        for col in pivot_data:
            f.write(f"{col:14}")
        f.write(f"{'   Grand Total':14}\n")
        f.write("-" * (25 + 14 * (len(pivot_data.keys()) + 1)) + "\n")

        # Print each row
        for row in unique_rows:
            f.write(f"{row:25}")
            row_total = 0
            for col in pivot_data.keys():
                value = pivot_data[col].get(row, 0)
                f.write(f"{value:14,.2f}")
                row_total += value
            f.write(f"{row_total:14,.2f}\n")

        f.write("-" * (25 + 14 * (len(pivot_data.keys()) + 1)) + "\n")

        # Print grand totals
        f.write(f"{'Grand Total':25}")
        for col in pivot_data.keys():
            f.write(f"{col_totals[col]:14,.2f}")
        f.write(f"{sum(col_totals.values()):14,.2f}\n")

        f.write(f"\n\nGenerated at {datetime.now()}\n")


def clean_pivot_data(pivot_data: Dict[str, Dict[str, float]]) -> Dict[str, Dict[str, float]]:
    """Clean pivot data by removing empty rows and columns."""
    # Sort the columns
    sorted_columns = sorted(pivot_data.keys())

    # Sort rows and filter out zero totals
    all_rows = set(row for col_data in pivot_data.values() for row in col_data.keys())
    row_totals = {row: sum(pivot_data[col].get(row, 0) for col in sorted_columns) for row in all_rows}
    sorted_rows = sorted([row for row in all_rows if row_totals[row] != 0], key=str.lower)

    # Filter out zero-sum columns
    filtered_columns = {col: pivot_data[col] for col in sorted_columns if sum(pivot_data[col].values()) != 0}

    # Create clean data
    clean_data = {}
    for col in filtered_columns:
        clean_data[col] = {}
        for row in sorted_rows:
            if row in pivot_data[col]:
                clean_data[col][row] = pivot_data[col][row]

    return clean_data


def main():
    """Main function to run the tax HIFO calculator."""
    init_files()
    transactions = get_transactions()

    # Find duplicates and all symbols
    symbols, duplicates = find_symbols(transactions)

    # Create summary report
    summary = [['year', 'symbol', 'total_gain_loss', 'total_income']]

    # Process each symbol
    for symbol in symbols:
        buy_sell_pairs, unsold = calculate_buy_sell_pairs(transactions, symbol)
        incomes = [txn for txn in transactions
                  if txn['symbol_normalized'] == symbol.lower()
                  and txn['txn_type'] == 'income']

        create_report(symbol, buy_sell_pairs, unsold, incomes)

        # Append to detail file
        with open(TAX_HIFO_DETAIL_OUTPUT, 'a', newline='') as file:
            writer = csv.writer(file)
            for row in buy_sell_pairs:
                writer.writerow([
                    symbol,
                    row['buy_date'].strftime('%Y-%m-%d'),
                    row['sell_date'].strftime('%Y-%m-%d'),
                    row['qty'],
                    f"{row['cost_basis']:.2f}",
                    f"{row['proceeds']:.2f}",
                    f"{row['gain_loss']:.2f}",
                    row['duration_held'],
                    row['sell_date'].strftime('%Y'),
                    'ST' if int(row['duration_held']) < 365 else 'LT',
                    row['buy_chain'],
                    row['buy_id'],
                    row['sell_chain'],
                    row['sell_id'],
                ])

        # Create yearly summary
        years = {pair['sell_date'].year for pair in buy_sell_pairs}
        years.update({income['date'].year for income in incomes})

        for year in years:
            yearly_gain_loss = sum(pair['gain_loss']
                                 for pair in buy_sell_pairs
                                 if pair['sell_date'].year == year)
            yearly_income = sum(income['usd_value']
                              for income in incomes
                              if income['date'].year == year)
            summary.append([year, symbol, yearly_gain_loss, yearly_income])

    # Save summary
    with open(TAX_HIFO_OUTPUT, 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerows(summary)

    # Write pivot tables
    gain_loss_pivot = pivot_table('year', 'symbol', 'total_gain_loss', summary)
    gain_loss_pivot = clean_pivot_data(gain_loss_pivot)
    write_pivot(gain_loss_pivot, TAX_HIFO_PIVOT_GAINLOSS_OUTPUT)

    income_pivot = pivot_table('year', 'symbol', 'total_income', summary)
    income_pivot = clean_pivot_data(income_pivot)
    write_pivot(income_pivot, TAX_HIFO_PIVOT_INCOME_OUTPUT)


if __name__ == "__main__":
    main()
