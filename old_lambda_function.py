import cbpro
import pandas as pd

c = cbpro.PublicClient()

# Get all the data

tickers = {
    'BTC': [7, 22, -1],
    'ETH': [10, 16, -1],
    'SOL': [7, 10, 46],
    'MATIC': [11, 25, -1],
    'AVAX': [5, 18, -1],
    'DOT': [8, 16, 47],
    'ADA': [11, 13, -1],
    'LUNA': [11, 20, -1]
}

# Set the start date to January 1st, 2020
jan20 = "2020-01-01T00:00:00Z"
may20 = "2020-05-31T00:00:00Z"
jun20 = "2020-06-01T00:00:00Z"
dec20 = "2020-12-31T00:00:00Z"
jan21 = "2021-01-01T00:00:00Z"
may21 = "2021-05-31T00:00:00Z"
jun21 = "2021-06-01T00:00:00Z"
dec21 = "2021-12-31T00:00:00Z"
jan22 = "2022-01-01T00:00:00Z"
may22 = "2022-05-31T00:00:00Z"
jun22 = "2022-06-01T00:00:00Z"
dec22 = "2022-12-31T00:00:00Z"
jan23 = "2023-01-01T00:00:00Z"

for ticker in tickers:
    shortSMA = 0
    midSMA = 0
    longSMA = 0
    historical = pd.DataFrame(c.get_product_historic_rates(product_id=ticker + '-USD',
                                                           granularity=86400, start=jan20,
                                                           end=may20))
    historical = historical.append(pd.DataFrame(c.get_product_historic_rates(product_id=ticker + '-USD',
                                                                             granularity=86400, start=jun20,
                                                                             end=dec20)))
    historical = historical.append(pd.DataFrame(c.get_product_historic_rates(product_id=ticker + '-USD',
                                                                             granularity=86400, start=jan21,
                                                                             end=may21)))
    historical = historical.append(pd.DataFrame(c.get_product_historic_rates(product_id=ticker + '-USD',
                                                                             granularity=86400, start=jun21,
                                                                             end=dec21)))
    historical = historical.append(pd.DataFrame(c.get_product_historic_rates(product_id=ticker + '-USD',
                                                                             granularity=86400, start=jan22,
                                                                             end=may22)))
    historical = historical.append(pd.DataFrame(c.get_product_historic_rates(product_id=ticker + '-USD',
                                                                             granularity=86400, start=jun22,
                                                                             end=dec22)))
    historical = historical.append(pd.DataFrame(c.get_product_historic_rates(product_id=ticker + '-USD',
                                                                             granularity=86400, start=jan23)))

    historical.columns = ["Date", "Open", "High", "Low", "Close", "Volume"]
    historical['Date'] = pd.to_datetime(historical['Date'], unit='s')
    historical.set_index('Date', inplace=True)
    historical.sort_values(by='Date', ascending=True, inplace=True)

    for i in range(5, 51):
        historical[str(i) + ' SMA'] = historical.Close.rolling(i).mean()
        if i == tickers[ticker][0]:
            shortSMA = float(historical.tail(1)[str(i) + ' SMA'])
        if i == tickers[ticker][1]:
            midSMA = float(historical.tail(1)[str(i) + ' SMA'])
        if i == tickers[ticker][2]:
            longSMA = float(historical.tail(1)[str(i) + ' SMA'])

    book = c.get_product_ticker(product_id=ticker + '-USD')
    livePrice = float(book['price'])

    print(ticker, 'live:', livePrice)
    print('short:', shortSMA)
    print('mid:', midSMA)
    print('long:', longSMA)
    print()

    historical.to_csv('./coin_data/' + ticker + '.csv', index=True, header=True)

print('End of File')