import pandas as pd
import numpy as np
import sys
from config import FLATTEN_OUTPUT, STABLECOINS

def concat(s) -> str:
    max_len = 30
    return s if len(str(s)) <= max_len else s[:max_len] + '...'


def categorize(row) -> str:
    # buy = receive amt > 0, send amt not NaN
    # receive_other (income or bridge) = receive amt > 0, send amt NaN
    # sell = receive amt not NaN, send amt > 0
    # stake = receive amt NaN, send amt > 0, certain project + tx names
    # sell_other (bridge) = receive amt NaN, send > 0

    if row['receives.amount'] > 0 and not pd.isna(row['sends.amount']):
        if row['sends.token.symbol'].lower() in STABLECOINS:
            return 'buy'
        else:
            return 'buysell'
    elif row['receives.amount'] > 0 and pd.isna(row['sends.amount']):
        if row['tx.name'] is not None and \
            f"{str(row['tx.name']).lower()}" in [
            "claim",
        ]:
            return 'income'
        else:
            return 'receive_other'
    elif not pd.isna(row['receives.amount']) and row['sends.amount'] > 0:
        if row['receives.token.symbol'].lower() in STABLECOINS:
            return 'sell'
        else:
            return 'sellbuy'
    elif pd.isna(row['receives.amount']) and row['sends.amount'] > 0:
        if f"{str(row['project.name']).lower()}:{row['tx.name'].lower()}" in [
            "concentrator:create_lock",
            "concentrator:increase_amount",
        ]:
            return 'stake'
        else:
            return 'sell_other'
    else:
        return np.nan


def main(token: str) -> None:
    # Read the CSV
    df = pd.read_csv(FLATTEN_OUTPUT)

    # Filter by the token
    df = df[(df['receives.token.symbol'].str.lower() == token.lower()) |
            (df['sends.token.symbol'].str.lower() == token.lower())].copy()
    df = df.sort_values(by=['time_at'])
    df['date'] = pd.to_datetime(df['time_at'], unit='s')

    # Categories
    df['category'] = df.apply(lambda row: categorize(row), axis=1)

    # Calculate cumulative receives
    df['rcumul'] = float('nan')
    condition = (df['receives.token.symbol'].str.lower() == token.lower())
    df.loc[condition, 'rcumul'] = df.loc[condition, 'receives.amount'].cumsum()

    # Calculate cumulative sends
    df['scumul'] = float('nan')
    condition = (df['sends.token.symbol'].str.lower() == token.lower())
    df.loc[condition, 'scumul'] = df.loc[condition, 'sends.amount'].cumsum()

    # Concat obnoxiously long transaction names
    df['tx.name'] = df['tx.name'].apply(concat)

    # Replace NaNs with dashes
    df = df.fillna('-')

    # Shorten column names
    df.rename(columns={
        'receives.token.symbol': 'rsym',
        'receives.amount': 'ramt',
        'sends.token.symbol': 'ssym',
        'sends.amount': 'samt',
        'cate_id': 'cat',
        'project.chain': 'chain',
        'project.name': 'project',
        'tx.name': 'tx',
    }, inplace=True)

    # Basic pd formatting options
    pd.set_option('display.max_rows', None)  # Display unlimited rows
    pd.set_option('display.float_format', '{:.2f}'.format)

    # Print the dataframe
    print(f"Flatten Log for {token}")
    print(df[[
        'date', 
        'ramt', 
        'rsym',
        'samt', 
        'ssym',
        'chain',
        'cat',
        'project',
        'tx',
        'rcumul',
        'scumul',
        'category',
        ]].to_string(index=False, header=True))


if __name__ == '__main__':

    if len(sys.argv) > 1:
        token = sys.argv[1]
        main(token)
    else:
        print(f"Usage: python3 {sys.argv[0].split('/')[-1]} <token>")
