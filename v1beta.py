# Section 1
import krakenex
import psycopg2
import time
from datetime import datetime, timedelta

# Import Kraken API and PostgreSQL credentials from local files
from numpy.core.defchararray import lower

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

# Make a Kraken API call to get the balance of USD in my account and print it out
response = api.query_private('Balance')
usd_balance = response['result']['ZUSD']
print('USD Balance:', usd_balance)

cur.execute('SELECT SUM(newinvestments) FROM coinBalances')
newInvestments = cur.fetchone()[0]
print('newInvestments', newInvestments)

# Make a database query to get the coinbalance table and print it out nicely
cur.execute('SELECT * FROM coinBalances')
coin_balances = cur.fetchall()
print('coinBalances:')
coinTickers = []
for row in coin_balances:
    print(row)
    coinTickers += [row[1]]
print('coinTickers', coinTickers)

# If any of the above 3 requests return errors or fail, then do not proceed. Print a helpful error message
if kraken_time is None or coin_balances is None:
    print("Error: Unable to retrieve data from either Kraken API or PostgreSQL database")
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
        cur.execute("SELECT transactionId FROM alltransactions")
        transactions = [transaction[0] for transaction in cur.fetchall()]
        print('alltransactions:', transactions)
        # Process the trades as needed
        for my_trade in trades:
            print('Trade: ', trades[my_trade])
            if trades[my_trade]['pair'].strip('USD') in coinTickers and trades[my_trade]['ordertxid'] not in transactions:
                # do something with the trade data
                trade = trades[my_trade]
                coinTicker = trade['pair'].strip('USD')
                date = datetime.fromtimestamp(trade['time']).strftime("%Y-%m-%d")
                direction = trade['type']
                fee_type = trade['ordertype']
                price = trade['price']
                volume = trade['vol']
                fee = float(trade['fee'])
                cost = float(trade['cost'])
                id = trade['ordertxid']

                cur.execute(f"INSERT INTO {lower(coinTicker)}_transactions (date, direction, fee_type, price) VALUES (\'{date}\', \'{direction}\', \'{fee_type}\', {price})")
                conn.commit()

                cur.execute(f"INSERT INTO alltransactions (transactionid) VALUES (\'{id}\')")
                conn.commit()

                if direction == 'buy':
                    cur.execute(f"UPDATE coinBalances SET boughtin = true, usd = 0, coinamount = {volume}, totalfees = totalfees + {fee}, newinvestments = 0 WHERE coinTicker = \'{coinTicker}\'")
                    conn.commit()
                else:
                    cur.execute(f"UPDATE coinBalances SET boughtin = false, usd = {cost - fee}, coinamount = {volume}, totalfees = totalfees + {fee}, newinvestments = 0 WHERE coinTicker = \'{coinTicker}\'")
                    conn.commit()
                    cur.execute(f"UPDATE coinBalances SET netGains = usd - totalInvested, netMultiplier = usd / totalInvested WHERE coinTicker = \'{coinTicker}\'")
                    conn.commit()


    for coinTicker in smaValues.keys():

        short = int(smaValues[coinTicker]['short'])
        medium = int(smaValues[coinTicker]['medium'])

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
        response = api.query_public('OHLC', data=payload)

        # Extract the prices
        prices = []
        for item in response['result'][list(response['result'])[0]]:
            prices.append(float(item[1]))  # Opening price at midnight

        # Calculate the simple moving averages for this coin at the length of {short} and {medium} sma lengths based on this data and the values of short and medium in this coinTicker's row of smaValues table.
        short_sma = sum(prices[-short:]) / short
        medium_sma = sum(prices[-medium:]) / medium

        sma_date = datetime.now().strftime('%Y-%m-%d')
        open_price = prices[-1]

        try:
            cur.execute(f"INSERT INTO {lower(coinTicker)}_smaTargets (date, short, medium, open) VALUES (\'{sma_date}\', {short_sma}, {medium_sma}, {open_price})")
            conn.commit()
            print("Inserted sma targets for", coinTicker)
        except:
            conn.rollback()
            print("Targets exist already for", coinTicker)

        cur.execute(f"SELECT MAX(date) FROM {coinTicker}_transactions")
        try:
            latest_transaction = cur.fetchone()[0]
        except:
            latest_transaction = 'None'
        print("Latest Transaction", latest_transaction)
        print("SMA Date", sma_date)

        if str(latest_transaction) != str(sma_date):
            print(f"Beginning {coinTicker} evaluations:")
            # Evaluate if this coin is boughtIn
            stringOfCoinTicker = f"\'{coinTicker}\'"
            cur.execute(f"SELECT * FROM coinBalances WHERE coinTicker = {stringOfCoinTicker}")
            coin_balances = cur.fetchall()[0]
            print(coinTicker, 'balance:', coin_balances)
            boughtIn = bool(coin_balances[2])
            order_price = max(short_sma, medium_sma)
            buy_cash = float(coin_balances[3]) + float(coin_balances[7])
            coin_amount = float(coin_balances[4])

            # Call the 'Ticker' public API endpoint to get the live price of BTC/USD
            response = api.query_public('Ticker', {'pair': pair})

            # Extract the live price from the response
            live_price = response['result'][pair]['c'][0]

            print(f"The live price of {coinTicker} is {live_price}")

            if buy_cash + coin_amount > 0:
                # If we are not boughtIn
                if not boughtIn:
                    # Place limit order
                    if live_price > order_price:
                        print(f"Placing limit buy order on {coinTicker}")
                        retry_count = 0
                        while retry_count < 10:
                            try:
                                response = api.query_private("AddOrder", {
                                    "pair": pair,
                                    "type": "buy",
                                    "ordertype": "market",
                                    "price": round(order_price, 4),
                                    "volume": buy_cash / order_price,
                                    "oflags": "post"
                                })
                                print("Order:", {
                                    "pair": pair,
                                    "type": "buy",
                                    "ordertype": "limit",
                                    "price": round(order_price, 4),
                                    "volume": buy_cash / order_price,
                                    "oflags": "post"
                                })
                                if response["error"]:
                                    raise Exception(response["error"])
                                else:
                                    print("Limit order has been set or updated.")
                                    print(response['result'])
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
                                    "volume": max_volume,
                                    "oflags": "post"
                                })
                                if response["error"]:
                                    raise Exception(response["error"])
                                else:
                                    print("Market transaction successful!")
                                    print(response['result'])
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
                                    "price": order_price,
                                    "volume": coin_amount,
                                    "oflags": "post"
                                })
                                if response["error"]:
                                    raise Exception(response["error"])
                                else:
                                    print("Limit order has been set or updated.")
                                    print(response['result'])
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
                                    "volume": coin_amount,
                                    "oflags": "post"
                                })
                                if response["error"]:
                                    raise Exception(response["error"])
                                else:
                                    print("Market transaction successful!")
                                    print(response['result'])
                                    break
                            except Exception as e:
                                print("Error making market transaction: {}".format(e))
                                print("Retrying in 10 seconds...")
                                time.sleep(10)
                                retry_count += 1
                        else:
                            print("Maximum retry count reached. Unable to make market transaction.")
                    print()
            else:
                print("No money invested for this coin yet.")
        else:
            print("Transaction already occurred today.")
        print("Finished")
