from datetime import datetime
import csv
from config import PRICE_OUTPUT


def get_transactions() -> list:
    # Read the CSV file
    with open(PRICE_OUTPUT, 'r') as file:
        reader = csv.DictReader(file)
        transactions = [row for row in reader]
        return transactions


def calculate_hifo_gains_losses(transactions, target_symbol):
    # Filter transactions by the target symbol
    transactions = [txn for txn in transactions if txn['symbol'].lower() == target_symbol.lower()]

    # Separate buys/incomes and sells
    buys = [txn for txn in transactions if txn['txn_type'] in ['buy', 'income']]
    print()
    print(f"Number of buy/income transactions: {len(buys)}")
    print(f"Qty of buy/income transactions: {sum(float(txn['qty']) for txn in buys):,.8f}")

    sells = [txn for txn in transactions if txn['txn_type'] == 'sell']
    print(f"Number of sell transactions: {len(sells)}")
    print(f"Qty of sell transactions: {sum(float(txn['qty']) for txn in sells):,.8f}")
    print()
    print(f"Remaining {target_symbol}: {sum(float(txn['qty']) for txn in buys) - sum(float(txn['qty']) for txn in sells):,.8f}")
    print()

    # Sort buys/incomes by unit value in descending order (HIFO)
    buys.sort(key=lambda x: float(x['usd_value']) / float(x['qty']), reverse=True)

    results = []

    for sell in sells:
        sell_qty = float(sell['qty'])
        sell_usd_value = float(sell['usd_value'])
        sell_unit_price = float(sell['usd_value']) / float(sell['qty'])
        sell_date = datetime.strptime(sell['date'], '%Y-%m-%d %H:%M:%S')
        print(f"{sell_date} Sell {sell_qty} {target_symbol} for ${sell_usd_value:,.2f} (${sell_unit_price:,.2f} per)")

        # Filter out buys/incomes that happened after the sell date
        valid_buys = [buy for buy in buys if buy['date'] <= sell['date']]

        while sell_qty > 0 and valid_buys:
            buy = valid_buys[0]

            buy_qty_available = float(buy['qty'])
            buy_unit_price = float(buy['usd_value']) / float(buy['qty'])
            buy_date = datetime.strptime(buy['date'], '%Y-%m-%d %H:%M:%S')

            if buy_qty_available <= sell_qty:
                buy_qty_sold = buy_qty_available
                sell_usd_value = buy_qty_sold * sell_unit_price
                gain_loss = (buy_qty_sold * sell_unit_price) - (buy_qty_sold * buy_unit_price)
                duration_held = (sell_date - buy_date).days
                results.append({
                    'buy_date': buy['date'],
                    'sell_date': sell['date'],
                    'qty': buy_qty_sold,
                    'gain_loss': gain_loss,
                    'duration_held': duration_held
                })
                sell_qty -= buy_qty_sold
                print(f"- Matched {buy_date} {buy_qty_sold:.4f} for ${sell_usd_value:,.2f} (${buy_unit_price:,.2f} per), Gain/loss: ${gain_loss:,.2f}, Held: {duration_held} days, Qty still to Sell: {sell_qty:.4f}")

                index_to_remove = buys.index(buy)
                buys.pop(index_to_remove)  # Remove the buy/income transaction from the original list
                valid_buys.pop(0)
            else:
                buy_qty_sold = sell_qty
                partial_buy_value = buy_qty_sold * buy_unit_price
                gain_loss = (buy_qty_sold * sell_unit_price) - (buy_qty_sold * buy_unit_price)
                duration_held = (sell_date - buy_date).days
                results.append({
                    'buy_date': buy['date'],
                    'sell_date': sell['date'],
                    'qty': buy_qty_sold,
                    'gain_loss': gain_loss,
                    'duration_held': duration_held
                })
                sell_qty = 0
                print(f"- Partial {buy_date} for {buy_qty_sold:.4f} / {buy_qty_available:.4f} for ${partial_buy_value:,.2f} (${buy_unit_price:.2f} per), Gain/loss: ${gain_loss:,.2f}, Held: {duration_held} days, Qty still to Sell: {sell_qty:.4f}")
                index_to_update = buys.index(buy)
                buys[index_to_update]['qty'] = str(buy_qty_available - buy_qty_sold)
                buys[index_to_update]['usd_value'] = str(partial_buy_value)
                # buy_income['qty'] = str(float(buy_income['qty']) - qty_to_sell)

    # Remaining unsold assets
    unsold_assets = [{
        'buy_date': buy_income['date'],
        'buy_qty': buy_income['qty'],
        'usd_value': buy_income['usd_value']
    } for buy_income in buys if float(buy_income['qty']) > 0]

    return results, unsold_assets


def determine_qty_remaining(transactions, target_symbol):
    # Filter transactions by the target symbol
    transactions = [txn for txn in transactions if txn['symbol'].lower() == target_symbol.lower()]

    # Sum up the quantities of buys/incomes and subtract the quantities of sells
    buy_qty = sum(float(txn['qty']) for txn in transactions if txn['txn_type'] in ['buy', 'income'])
    sell_qty = sum(float(txn['qty']) for txn in transactions if txn['txn_type'] == 'sell')

    return buy_qty, sell_qty


def aggregate_results_by_year(results):
    yearly_data = {}

    for result in results:
        year = datetime.strptime(result['sell_date'], '%Y-%m-%d %H:%M:%S').year
        if year not in yearly_data:
            yearly_data[year] = {
                'qty_sold': 0,
                'total_gain_loss': 0
            }
        yearly_data[year]['qty_sold'] += float(result['qty'])
        yearly_data[year]['total_gain_loss'] += float(result['gain_loss'])

    return yearly_data


def main():
    transactions = get_transactions()
    symbol = 'eth'  # Change this to the desired symbol

    # buy_qty, sell_qty = determine_qty_remaining(transactions, symbol)
    # print(f"Total buys/incomes for symbol {symbol}: {buy_qty:.8f}")
    # print(f"Total sells for symbol {symbol}: {sell_qty:.8f}")
    # print(f"Remaining quantity for symbol {symbol}: {buy_qty - sell_qty:.8f}")

    results, unsold = calculate_hifo_gains_losses(transactions, symbol)

    print(f"\nCapital Gains/Losses and Duration Held for symbol {symbol}:")
    for result in results:
        print(f"Buy Date: {result['buy_date']}, Sell Date: {result['sell_date']}, Qty: {float(result['qty']):.4f}, Gain/Loss: ${result['gain_loss']:.2f}, Duration Held: {result['duration_held']} days")

    print("\nUnsold Assets:")
    for asset in unsold:
        print(f"Buy Date: {asset['buy_date']}, Buy Qty: {float(asset['buy_qty']):,.4f}, USD Value: ${float(asset['usd_value']):,.2f}, Unit Cost: ${float(asset['usd_value'])/float(asset['buy_qty']):,.2f}")
    print(f"\nRemaining {symbol}: {sum([float(asset['buy_qty']) for asset in unsold]):,.4f}")

    yearly_aggregated_data = aggregate_results_by_year(results)

    for year, data in yearly_aggregated_data.items():
        print(f"\nYear: {year}")
        print(f"Quantity Sold: {data['qty_sold']:,.4f}")
        print(f"Total Capital Gains/Losses: ${data['total_gain_loss']:,.2f}")


if __name__ == "__main__":
    main()
