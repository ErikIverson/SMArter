import cbpro
import pandas as pd

# Define the start and end dates for the historical data
import datetime

# Define the start and end dates for the loop
start_date = datetime.date(2021, 10, 27)
# end_date = datetime.date(2023, 2, 12)
end_date = datetime.date(2023, 2, 12)


# Define a timedelta of 1 day
delta = datetime.timedelta(days=1)
ticker = "ETH"
# Connect to the Coinbase Pro API
c = cbpro.PublicClient()

# Define the time interval for the historical data
granularity = 3600 # 4 hours
historical = pd.DataFrame()

# Iterate over the dates using a for loop
current_date = start_date
data = pd.DataFrame(c.get_product_historic_rates(product_id=ticker + "-USD", start=str(current_date),
                                                 end=str(current_date + delta), granularity=granularity))
historical_temp = pd.DataFrame(data)
print(current_date)
current_date += delta
historical = pd.concat([historical, historical_temp])

historical.columns= ["Date","Low","High","Open","Close","Volume"]
historical['Date'] = pd.to_datetime(historical['Date'], unit='s')
historical.set_index('Date', inplace=True)
historical.sort_values(by='Date', ascending=True, inplace=True)
# historical = historical.drop_duplicates()
historical.to_csv('./coin_data_hourly/' + ticker + '-test.csv', index=True, header=True)