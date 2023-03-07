# Section 1
import krakenex
import psycopg2
import time
from datetime import datetime, timedelta

# Import Kraken API and PostgreSQL credentials from local files
from kraken_credentials import api_key, api_secret
from postgres_credentials import db_name, db_user, db_password, db_host, db_port

# Open connection to PostgreSQL database
conn = psycopg2.connect(database=db_name, user=db_user, password=db_password, host=db_host, port=db_port)
cur = conn.cursor()

# Create a Kraken API object with credentials
api = krakenex.API(key=api_key, secret=api_secret)

# Make a Kraken API call to get the time from Kraken
kraken_time = api.query_public('Time')
print('Kraken Time:', kraken_time['result']['rfc1123'])

# Make a Kraken API call to get the balance of USDC in my account and print it out
usdc_balance = api.query_private('Balance', {'asset': 'USDC'})['result']['USDC']
print('USDC Balance:', usdc_balance)

cur.execute('SELECT SUM(newinvestments) FROM coinBalances')
newInvestments = cur.fetchone()
print('newInvestments', newInvestments)

# Make a database query to get the coinbalance table and print it out nicely
cur.execute('SELECT * FROM coinBalances')
coin_balances = cur.fetchall()
print('coinBalances:')
for row in coin_balances:
    print(row)


# If any of the above 3 requests return errors or fail, then do not proceed. Print a helpful error message
if kraken_time is None or coin_balances is None:
    print("Error: Unable to retrieve data from either Kraken API or PostgreSQL database")
elif usdc_balance == 0:
    print("Empty USDC Balance")
else:
    smaValues = {}
    cur.execute('SELECT * FROM smaValues')
    smaValues_rows = cur.fetchall()
    for row in smaValues_rows:
        smaValues[row[1]] = {'short': row[2], 'medium': row[3]}
    print(smaValues)

    # Get the current time and the time 24 hours ago
    now = datetime.utcnow()
    last_day = now - timedelta(days=1)

    # Convert the times to the format expected by Kraken
    since = str(int(time.mktime(last_day.timetuple())))
    end = str(int(time.mktime(now.timetuple())))

    # Get any filled trades from the last 24 hours and update tables
    response = api.query_private('TradesHistory', {'start': since, 'end': end})

    if response['error']:
        print('Error making Kraken API request:', response['error'])
    else:
        # Extract the list of trades from the response
        trades = response['result']['trades']

    # Process the trades as needed
    for trade in trades:
        # do something with the trade data
        coinTicker = trade['pair'][1:-4]
        date = datetime.datetime.fromtimestamp(trade['time']).strftime("%Y-%m-%d %H:%M:%S")
        direction = trade['type']
        fee_type = trade['ordertype']
        price = trade['price']
        volume = trade['vol']
        fee = trade['fee']
        cost = trade['cost']

        cur.execute(f"INSERT INTO {coinTicker}_transactions (date, direction, fee_type, price) VALUES ({date}, {direction}, {fee_type}, {price}")
        
        if direction == 'buy':
            cur.execute(f"UPDATE coinBalances SET boughtin = true, usdc = 0, coinamount = {volume}, totalfees = totalfees + {fee}, newinvestments = 0 WHERE coinTicker = {coinTicker}")
        else:
            cur.execute(f"UPDATE coinBalances SET boughtin = false, usdc = {cost - fee}, coinamount = {volume}, totalfees = totalfees + {fee}, totalnewinvestments = 0, netGains = usdc - totalInvestments, netMultiplier = usdc / totalInvestments WHERE coinTicker = {coinTicker}")


    for coinTicker in smaValues.keys():
          
        short = smaValues[coinTicker]['short']
        medium = smaValues[coinTicker]['medium']

        # Set API endpoint and parameters
        pair = coinTicker + 'USD'
        interval = 1440  # 1 day interval
        since = int(time.time() - (30*24*60*60)) # 30 days ago (in seconds)

        # Set request parameters
        payload = {
            'pair': pair,
            'interval': interval,
            'since': since
        }

        # Send request to Kraken API
        response = api.query_private('OHLC', data=payload)

        # Extract the prices
        prices = []
        for item in response['result'][list(response['result'])[0]]:
            prices.append(item[1])  # Opening price at midnight

        # Calculate the simple moving averages for this coin at the length of {short} and {medium} sma lengths based on this data and the values of short and medium in this coinTicker's row of smaValues table.
        short_sma = sum(prices[-short:]) / short
        medium_sma = sum(prices[-medium:]) / medium

        sma_date = datetime.datetime.now().strftime('%Y-%m-%d')
        open_price = prices[-1][1]
        cur.execute(f"INSERT INTO {coinTicker}_smaTargets (date, short, medium, open) VALUES ('{sma_date}', {short_sma}, {medium_sma}, {open_price})")

        latest_transaction = cur.execute(f"SELECT MAX(date) FROM {coinTicker}_transactions").fetchone()
        print("Latest Transaction", latest_transaction)

        if latest_transaction != sma_date:
            print(f"Beginning {coinTicker} evaluations:")
            # Evaluate if this coin is boughtIn
            coin_balances = cur.execute(f"SELECT * FROM coinBalances WHERE coinTicker = {coinTicker}").fetchall()
            boughtIn = coin_balances[2]
            order_price = max(short_sma, medium_sma)
            buy_cash = coin_balances[3] + coin_balances[7]
            coin_amount = coin_balances[4]

            # If we are not boughtIn
            if not boughtIn:
                # Place limit order
                if open_price < order_price:
                    print(f"Placing limit buy order on {coinTicker}")
                    retry_count = 0
                    while retry_count < 10:
                        try:
                            response = api.query_private("AddOrder", {
                                "pair": pair,
                                "type": "buy",
                                "ordertype": "limit",
                                "price": str(order_price),
                                "volume": str(buy_cash / order_price),
                                "oflags": "post"
                            })
                            if response["error"]:
                                raise Exception(response["error"])
                            else:
                                print("Limit order has been set or updated.")
                                break
                        except Exception as e:
                            print("Error setting or updating limit order: {}".format(e))
                            print("Retrying in 10 seconds...")
                            time.sleep(10)
                            retry_count += 1
                    else:
                        print("Maximum retry count reached. Unable to set or update limit order.")
                
                # Place Market Order
                else:
                    print(f"Placing market buy order on {coinTicker}")
                    # Calculate the maximum volume we can buy with our available cash
                    ticker_response = api.query_public("Ticker", {"pair": pair})
                    last_trade_price = float(ticker_response["result"][pair]["c"][0])
                    max_volume = buy_cash / last_trade_price
                    retry_count = 0
                    while retry_count < 10:
                        try:
                            response = api.query_private("AddOrder", {
                                "pair": pair,
                                "type": "buy",
                                "ordertype": "market",
                                "volume": str(max_volume),
                                "oflags": "post"
                            })
                            if response["error"]:
                                raise Exception(response["error"])
                            else:
                                print("Market transaction successful!")
                                break
                        except Exception as e:
                            print("Error making market transaction: {}".format(e))
                            print("Retrying in 10 seconds...")
                            time.sleep(10)
                            retry_count += 1
                    else:
                        print("Maximum retry count reached. Unable to make market transaction.")
            
            # If we are boughtIn
            else:
                # Place a limit sell order
                if open_price > order_price:
                    print(f"Placing limit sell order on {coinTicker}")
                    # Set or update a limit order with 3 retries
                    retry_count = 0
                    while retry_count < 10:
                        try:
                            response = api.query_private("AddOrder", {
                                "pair": pair,
                                "type": "sell",
                                "ordertype": "limit",
                                "price": str(order_price),
                                "volume": str(coin_amount),
                                "oflags": "post"
                            })
                            if response["error"]:
                                raise Exception(response["error"])
                            else:
                                print("Limit order has been set or updated.")
                                break
                        except Exception as e:
                            print("Error setting or updating limit order: {}".format(e))
                            print("Retrying in 10 seconds...")
                            time.sleep(10)
                            retry_count += 1
                    else:
                        print("Maximum retry count reached. Unable to set or update limit order.")
                
                # Place a market sell order
                else:
                    print(f"Placing market sell order on {coinTicker}")
                    retry_count = 0
                    while retry_count < 10:
                        try:
                            response = api.query_private("AddOrder", {
                                "pair": pair,
                                "type": "sell",
                                "ordertype": "market",
                                "volume": str(coin_amount),
                                "oflags": "post"
                            })
                            if response["error"]:
                                raise Exception(response["error"])
                            else:
                                print("Market transaction successful!")
                                break
                        except Exception as e:
                            print("Error making market transaction: {}".format(e))
                            print("Retrying in 10 seconds...")
                            time.sleep(10)
                            retry_count += 1
                    else:
                        print("Maximum retry count reached. Unable to make market transaction.")
                print()

        print("Finished")
