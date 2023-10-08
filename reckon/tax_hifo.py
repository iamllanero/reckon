from config import PRICE_OUTPUT, TAX_HIFO_OUTPUT, TAX_HIFO_PIVOT_OUTPUT
from datetime import datetime
import csv
import re


def get_transactions() -> list:
    # Read the CSV file
    with open(PRICE_OUTPUT, 'r') as file:
        reader = csv.DictReader(file)
        transactions = [row for row in reader]
        return transactions


def calculate_buy_sell_pairs(transactions, target_symbol):
    # Filter transactions by the target symbol
    transactions = [txn for txn in transactions if txn['symbol'].lower() == target_symbol.lower()]

    # Separate buys/incomes and sells
    buys = [txn for txn in transactions if txn['txn_type'] in ['buy', 'income']]
    # print()
    # print(f"Number of buy/income transactions: {len(buys)}")
    # print(f"Qty of buy/income transactions: {sum(float(txn['qty']) for txn in buys):,.8f}")

    sells = [txn for txn in transactions if txn['txn_type'] == 'sell']
    # print(f"Number of sell transactions: {len(sells)}")
    # print(f"Qty of sell transactions: {sum(float(txn['qty']) for txn in sells):,.8f}")
    # print()
    # print(f"Remaining {target_symbol}: {sum(float(txn['qty']) for txn in buys) - sum(float(txn['qty']) for txn in sells):,.8f}")
    # print()

    # Sort buys/incomes by unit value in descending order (HIFO)
    buys.sort(key=lambda x: float(x['usd_value']) / float(x['qty']), reverse=True)

    buy_sell_pairs = []

    for sell in sells:
        sell_qty = float(sell['qty'])
        sell_usd_value = float(sell['usd_value'])
        sell_unit_price = float(sell['usd_value']) / float(sell['qty'])
        sell_date = datetime.strptime(sell['date'], '%Y-%m-%d %H:%M:%S')

        # print(f"{sell_date} Sell {sell_qty} {target_symbol} for ${sell_usd_value:,.2f} (${sell_unit_price:,.2f} per)")

        # Filter out buys/incomes that happened after the sell date
        valid_buys = [buy for buy in buys if buy['date'] <= sell['date']]

        while sell_qty > 0 and valid_buys:
            buy = valid_buys[0]

            buy_qty_available = float(buy['qty'])
            buy_unit_price = float(buy['usd_value']) / float(buy['qty'])
            buy_date = datetime.strptime(buy['date'], '%Y-%m-%d %H:%M:%S')

            # Sell as much as possible from the buy transaction
            sold_qty = min(buy_qty_available, sell_qty)
            sold_usd_value = sold_qty * buy_unit_price
            gain_loss = (sold_qty * sell_unit_price) - (sold_qty * buy_unit_price)
            duration_held = (sell_date - buy_date).days

            buy_sell_pairs.append({
                'buy_date': buy['date'],
                'sell_date': sell['date'],
                'qty': sold_qty,
                'gain_loss': gain_loss,
                'duration_held': duration_held
            })

            # print(f"- Matched {buy_date} {sold_qty:.4f} for ${sold_usd_value:,.2f} (${buy_unit_price:,.2f} per), Gain/loss: ${gain_loss:,.2f}, Held: {duration_held} days, Qty still to Sell: {sell_qty - sold_qty:.4f}")

            if buy_qty_available <= sell_qty:
                index_to_remove = buys.index(buy)
                buys.pop(index_to_remove)  # Remove the buy/income transaction from the original list
                valid_buys.pop(0)
            else:
                index_to_update = buys.index(buy)
                buys[index_to_update]['qty'] = str(buy_qty_available - sold_qty)
                buys[index_to_update]['usd_value'] = str((buy_qty_available - sold_qty) * buy_unit_price)

            sell_qty -= sold_qty


    # Remaining unsold assets
    unsold_assets = [{
        'buy_date': buy_income['date'],
        'buy_qty': buy_income['qty'],
        'usd_value': buy_income['usd_value']
    } for buy_income in buys if float(buy_income['qty']) > 0]

    return buy_sell_pairs, unsold_assets


def determine_qty_remaining(transactions, target_symbol):
    # Filter transactions by the target symbol
    transactions = [txn for txn in transactions if txn['symbol'].lower() == target_symbol.lower()]

    # Sum up the quantities of buys/incomes and subtract the quantities of sells
    buy_qty = sum(float(txn['qty']) for txn in transactions if txn['txn_type'] in ['buy', 'income'])
    sell_qty = sum(float(txn['qty']) for txn in transactions if txn['txn_type'] == 'sell')

    return buy_qty, sell_qty


def aggregate_results_by_year(buy_sell_pairs):
    yearly_data = {}

    for result in buy_sell_pairs:
        year = datetime.strptime(result['sell_date'], '%Y-%m-%d %H:%M:%S').year
        if year not in yearly_data:
            yearly_data[year] = {
                'qty_sold': 0,
                'total_gain_loss': 0
            }
        yearly_data[year]['qty_sold'] += float(result['qty'])
        yearly_data[year]['total_gain_loss'] += float(result['gain_loss'])

    return yearly_data


def find_symbols(transactions):
    symbol_to_token_id = {}
    duplicates = {}
    symbols = set()

    for txn in transactions:
        symbol = txn['symbol']
        token_id = txn['token_id']
        symbols.add(symbol)
        if symbol in symbol_to_token_id:
            if token_id not in symbol_to_token_id[symbol]:
                symbol_to_token_id[symbol].append(token_id)
                duplicates[symbol] = symbol_to_token_id[symbol]
        else:
            symbol_to_token_id[symbol] = [token_id]

    return sorted(symbols), duplicates


def make_filename_safe(s, max_length=255):
    # Remove or replace invalid characters
    s = re.sub(r'[<>:"/\\|?*]', '_', s)  # Replace reserved characters with underscores
    s = re.sub(r'[\0-\31]', '', s)  # Remove control characters

    # Remove potentially problematic sequences
    s = s.replace('..', '_')

    # Truncate to max_length
    s = s[:max_length]

    return s


def create_report(symbol, buy_sell_pairs, unsold_assets, incomes):
    if not buy_sell_pairs and not unsold_assets and not incomes:
        print(f"No report for {symbol}")
        return

    # Create the report
    with open(f'output/tax_hifo/reports/{make_filename_safe(symbol)}.txt', 'w') as file:
        print(f"Creating report for {symbol}")
        file.write(f"Tax HIFO Report for {symbol}\n\n")
        remaining_qty = sum([float(asset['buy_qty']) for asset in unsold_assets])
        file.write(f"Remaining {symbol}: {sum([float(asset['buy_qty']) for asset in unsold_assets]):,.4f}\n")
        if remaining_qty > 0:
            file.write(f"Avg Unit Cost: ${sum([float(asset['usd_value']) for asset in unsold_assets]) / sum([float(asset['buy_qty']) for asset in unsold_assets]):,.2f}\n")

        years = set()
        years.update([datetime.strptime(buy_sell_pair['sell_date'], '%Y-%m-%d %H:%M:%S').year for buy_sell_pair in buy_sell_pairs])
        for year in sorted(years):
            yearly_buy_pairs = [buy_sell_pair for buy_sell_pair in buy_sell_pairs if datetime.strptime(buy_sell_pair['sell_date'], '%Y-%m-%d %H:%M:%S').year == year]
            yearly_incomes = [income for income in incomes if datetime.strptime(income['date'], '%Y-%m-%d %H:%M:%S').year == year]
            file.write("-------------------------------------------------------------------------------\n")
            file.write(f"Year {year}\n")
            file.write("-------------------------------------------------------------------------------\n")
            file.write(f"Number of Transactions: {len(yearly_buy_pairs)}\n")
            file.write(f"Quantity Sold: {sum([float(buy_sell_pair['qty']) for buy_sell_pair in yearly_buy_pairs]):,.4f}\n")
            file.write(f"Capital Gains/Loss: ${sum([float(buy_sell_pair['gain_loss']) for buy_sell_pair in yearly_buy_pairs]):,.2f}\n")
            file.write(f"Total Income: ${sum([float(income['usd_value']) for income in yearly_incomes]):,.2f}\n")

            if yearly_buy_pairs:
                file.write("\nBuy/Sell Pairs\n")
                file.write(f"Buy Date    Sell Date   Qty             Gain/Loss       Held\n")
                file.write( "----------  ----------  --------------  --------------  ----\n")
                for buy_sell_pair in yearly_buy_pairs:
                    sell_date = datetime.strptime(buy_sell_pair['sell_date'], '%Y-%m-%d %H:%M:%S')
                    if sell_date.year == year:
                        file.write(f"{buy_sell_pair['buy_date'][:10]}  ")
                        file.write(f"{buy_sell_pair['sell_date'][:10]}  ")
                        file.write(f"{buy_sell_pair['qty']:14,.4f}  ")
                        file.write(f"{buy_sell_pair['gain_loss']:14,.2f}  ")
                        file.write(f"{int(buy_sell_pair['duration_held']):>4}")
                        file.write("\n")
            
            if yearly_incomes:
                file.write("\nIncome\n")
                file.write(f"Date        Qty             USD Value\n")
                file.write( "----------  --------------  --------------\n")
                for income in yearly_incomes:
                    file.write(f"{income['date'][:10]}  ")
                    file.write(f"{float(income['qty']):14,.4f}  ")
                    file.write(f"{float(income['usd_value']):14,.4f}")
                    file.write("\n")

            file.write("\n")

        if unsold_assets:
            file.write("\nRemaining (Unsold) Assets\n")
            file.write(f"Buy Date    Qty             USD Value      Unit Cost\n")
            file.write( "----------  --------------  --------------  ------------\n")
            for asset in unsold_assets:
                file.write(f"{asset['buy_date'][:10]}  ")
                file.write(f"{float(asset['buy_qty']):14,.4f}  ")
                file.write(f"{float(asset['usd_value']):14,.2f}  ")
                file.write(f"{float(asset['usd_value']) / float(asset['buy_qty']):12,.2f}  ")
                file.write("\n")
        
        file.write(f"\n\nGenerated at {datetime.now()}\n")


def pivot_table(col, row, value, lines):
    pivot_data = {}
    header = lines[0]
    for line in lines[1:]:
        col_data = line[header.index(col)]
        row_data = line[header.index(row)]
        value_data = line[header.index(value)]
        if col_data not in pivot_data:
            pivot_data[col_data] = {}
        if row_data not in pivot_data[col_data]:
            pivot_data[col_data][row_data] = 0
        pivot_data[col_data][row_data] = value_data
    return pivot_data


def write_pivot(pivot_data):
   
    with open(TAX_HIFO_PIVOT_OUTPUT, 'w') as f:
        f.write("Tax HIFO Pivot Table\n\n")

        # Determine unique rows
        unique_rows = set()
        for row_data in pivot_data.values():
            for row in row_data.keys():
                unique_rows.add(row)
        unique_rows = sorted(list(unique_rows))

        # Calculate grand totals for columns
        col_totals = {}
        for col, row_data in pivot_data.items():
            col_totals[col] = sum(row_data.values())

        # Filter out columns that sum up to zero
        valid_cols = [col for col, total in col_totals.items() if total != 0]

        # Print header
        f.write(f"{'':25}")  # Empty space for the top-left corner of the table
        for col in sorted(valid_cols):
            f.write(f"{col:14}")
        f.write(f"{'   Grand Total':14}\n")  # Header for grand total column
        f.write("-" * (25 + 14 * (len(valid_cols) + 1)))  # Line under the header
        f.write("\n")

        # Print each row
        for row in unique_rows:
            f.write(f"{row:25}")
            row_total = 0  # Initialize row total
            for col in valid_cols:  # Iterate only over valid columns
                value = pivot_data[col].get(row, 0)  # Default to 0 if the row doesn't exist for this column
                f.write(f"{value:14,.2f}")
                row_total += value
            f.write(f"{row_total:14,.2f}\n")  # Print row total

        f.write("-" * (25 + 14 * (len(valid_cols) + 1)))  # Line under the rows
        f.write("\n")

        # Print grand totals for columns
        f.write(f"{'Grand Total':25}")
        for col in valid_cols:  # Iterate only over valid columns
            f.write(f"{col_totals[col]:14,.2f}")
        f.write(f"{sum(col_totals.values()):14,.2f}\n")  # Grand total of grand totals

        f.write(f"\n\nGenerated at {datetime.now()}\n")


def main():
    transactions = get_transactions()

    #Find duplicates and all symbols
    symbols, duplicates = find_symbols(transactions)
    # if duplicates:
    #     for symbol, token_ids in duplicates.items():
    #         print(f"Symbol: {symbol}, Token IDs: {token_ids}")
    

    # Create a summary report for: year, symbol, total gain/loss, total income
    summary = [['year', 'symbol', 'total_gain_loss', 'total_income']]

    # Create a detailed report for each symbol
    for symbol in symbols:
        buy_sell_pairs, unsold = calculate_buy_sell_pairs(transactions, symbol)
        incomes = [txn for txn in transactions if txn['symbol'].lower() == symbol.lower() and txn['txn_type'] == 'income']
        create_report(symbol, 
                      buy_sell_pairs, 
                      unsold,
                      incomes
        )

        years = set()
        years.update([datetime.strptime(buy_sell_pair['sell_date'], '%Y-%m-%d %H:%M:%S').year for buy_sell_pair in buy_sell_pairs])
        years.update([datetime.strptime(income['date'], '%Y-%m-%d %H:%M:%S').year for income in incomes])
        for year in years:
            summary.append([
                year,
                symbol,
                sum([float(buy_sell_pair['gain_loss']) for buy_sell_pair in buy_sell_pairs if datetime.strptime(buy_sell_pair['sell_date'], '%Y-%m-%d %H:%M:%S').year == year]),
                sum([float(income['usd_value']) for income in incomes if datetime.strptime(income['date'], '%Y-%m-%d %H:%M:%S').year == year])
            ])

    # Save summary
    with open(TAX_HIFO_OUTPUT, 'w') as file:
        writer = csv.writer(file)
        writer.writerows(summary)

    gain_loss_pivot = pivot_table('year', 'symbol', 'total_gain_loss', summary)
    write_pivot(gain_loss_pivot)



if __name__ == "__main__":
    main()
