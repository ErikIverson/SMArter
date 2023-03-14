import cbpro
import pandas as pd
import csv
from IPython.display import display

c = cbpro.PublicClient()

# Get all the data

tickers = [
    'BTC',
    'ETH',
    'SOL',
    'MATIC',
    'AVAX',
    'DOT',
    'ADA',
    'AXS',
    'XRP',
    'LTC',
    'DOGE',
    'AGIX',
    'FET',
    'LUNA'
    ]

# Load in the dates
for ticker in tickers:
    shortSMA = 0
    midSMA = 0
    longSMA = 0
# Open the CSV file for reading
    with open('OCT26_dates.xlsx', 'r') as file:

        # Create a CSV reader object
        reader = csv.reader(file)

        # Iterate over each row in the CSV file
        for date in reader:
            today = print(date[0])
            # historical = pd.DataFrame()
            # historical_temp = pd.DataFrame(c.get_product_historic_rates(product_id=ticker + "-USD", ))



    historical.columns= ["Date","Low","High","Open","Close","Volume"]
    historical['Date'] = pd.to_datetime(historical['Date'], unit='s')
    historical.set_index('Date', inplace=True)
    historical.sort_values(by='Date', ascending=True, inplace=True)
    historical = historical.drop_duplicates()

    for i in range(5,30):
        historical[str(i) + ' SMA'] = historical.Open.rolling(i).mean()

    display(historical)
    historical.to_csv('./coin_data/' + ticker + '.csv', index=True, header=True)

print('End of File')
