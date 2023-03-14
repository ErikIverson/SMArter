# Section 1
import krakenex
from sqlalchemy import create_engine, text
import time
from datetime import datetime, timedelta
import os

# Define the lambda_handler function
def lambda_handler(event, context):

    kraken_api_key = os.environ.get('KRAKEN_API_KEY')
    kraken_api_secret = os.environ.get('KRAKEN_API_SECRET')
    postgres_password = os.environ.get('POSTGRES_PASSWORD')
    postgres_host = os.environ.get('POSTGRES_HOST')


    # Open connection to PostgreSQL database
    engine = create_engine(f"postgresql://postgres:{postgres_password}@{postgres_host}:5432/postgres")

    # Open connection to PostgreSQL database
    conn = engine.connect()

    # Create a Kraken API object with credentials
    api = krakenex.API(key=kraken_api_key, secret=kraken_api_secret)

    ###################################################################################################################

    # Make a Kraken API call to get the time from Kraken
    kraken_time = api.query_public('Time')
    print('Kraken Time:', kraken_time['result']['rfc1123'])

    # Make a Kraken API call to get the balance of USD in my account and print it out
    response = api.query_private('Balance')
    usd_balance = response['result']['ZUSD']
    print('USD Balance:', usd_balance)

    result = conn.execute(text('SELECT SUM(newinvestments) FROM coinBalances'))
    newInvestments = result.fetchone()[0]
    print('newInvestments', newInvestments)

    # Make a database query to get the coinbalance table and print it out nicely
    result = conn.execute(text('SELECT * FROM coinBalances'))
    coin_balances = result.fetchall()
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
        result = conn.execute(text('SELECT * FROM smaValues'))
        smaValues_rows = result.fetchall()
        for row in smaValues_rows:
            smaValues[row[1]] = {'short': row[2], 'medium': row[3], 'decimals': row[4]}
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
            result = conn.execute(text("SELECT transactionId FROM alltransactions"))
            transactions = [transaction[0] for transaction in result.fetchall()]
            print('No. of transactions in the last 24 hrs:', len(trades))
            # Process the trades as needed
            for my_trade in trades:
                print('Trade: ', trades[my_trade])
                if trades[my_trade]['pair'][0] == 'X':
                    trades[my_trade]['pair'] = trades[my_trade]['pair'][1:]
                if trades[my_trade]['pair'].rstrip('ZUSD') in coinTickers and trades[my_trade][
                    'ordertxid'] not in transactions:
                    # do something with the trade data
                    trade = trades[my_trade]
                    coinTicker = trade['pair'].rstrip('ZUSD')
                    date = datetime.fromtimestamp(trade['time']).strftime("%Y-%m-%d")
                    time_of_trans = datetime.fromtimestamp(trade['time']).strftime("%H:%M:%S")
                    direction = trade['type']
                    fee_type = trade['ordertype']
                    price = trade['price']
                    volume = trade['vol']
                    fee = float(trade['fee'])
                    cost = float(trade['cost'])
                    id = trade['ordertxid']

                    conn.execute(text(
                        f"INSERT INTO {coinTicker.lower()}_transactions (date, direction, fee_type, price, time) VALUES (\'{date}\', \'{direction}\', \'{fee_type}\', {price}, \'{time_of_trans}\')"))
                    conn.commit()

                    conn.execute(text(f"INSERT INTO alltransactions (transactionid) VALUES (\'{id}\')"))
                    conn.commit()

                    if direction == 'buy':
                        conn.execute(text(
                            f"UPDATE coinBalances SET boughtin = true, usd = 0, coinamount = {volume}, totalfees = totalfees + {fee}, newinvestments = 0 WHERE coinTicker = \'{coinTicker}\'"))
                        conn.commit()
                        print("Trade processed.")
                    else:
                        conn.execute(text(
                            f"UPDATE coinBalances SET boughtin = false, usd = {cost - fee}, coinamount = {volume}, totalfees = totalfees + {fee}, newinvestments = 0 WHERE coinTicker = \'{coinTicker}\'"))
                        conn.commit()
                        conn.execute(text(
                            f"UPDATE coinBalances SET netGains = usd - totalInvested, netMultiplier = usd / totalInvested WHERE coinTicker = \'{coinTicker}\'"))
                        conn.commit()
                        print("Trade processed.")

        print("\n\n--------------------\n")
        for coinTicker in smaValues.keys():

            short = int(smaValues[coinTicker]['short'])
            medium = int(smaValues[coinTicker]['medium'])
            decimals = int(smaValues[coinTicker]['decimals'])

            # Set API endpoint and parameters
            pair = coinTicker + 'USD'
            interval = 1440  # 1 day interval
            since = int(time.time() - (30 * 24 * 60 * 60))  # 30 days ago (in seconds)

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

            sma_date = datetime.utcnow().strftime('%Y-%m-%d')
            open_price = prices[-1]

            try:
                conn.execute(text(
                    f"INSERT INTO {coinTicker.lower()}_smaTargets (date, short, medium, open) VALUES (\'{sma_date}\', {round(short_sma, 7)}, {round(medium_sma, 7)}, {open_price})"))
                conn.commit()
                print("Inserted sma targets for", coinTicker)
            except:
                conn.rollback()
                print("Targets exist already for", coinTicker)

            result = conn.execute(text(f"SELECT MAX(date) FROM {coinTicker}_transactions"))
            try:
                latest_transaction = result.fetchone()[0]
            except:
                latest_transaction = 'None'
            print("Latest Transaction", latest_transaction)
            print("SMA Date", sma_date)

            if str(latest_transaction) != str(sma_date):
                print(f"Beginning {coinTicker} evaluations:")
                # Evaluate if this coin is boughtIn
                stringOfCoinTicker = f"\'{coinTicker}\'"
                result = conn.execute(text(f"SELECT * FROM coinBalances WHERE coinTicker = {stringOfCoinTicker}"))
                coin_balances = result.fetchall()[0]
                print(coinTicker, 'balance:', coin_balances)
                boughtIn = bool(coin_balances[2])
                order_price = max(short_sma, medium_sma)
                buy_cash = float(coin_balances[3]) + float(coin_balances[7])
                coin_amount = round(float(coin_balances[4]), decimals)

                # Call the 'Ticker' public API endpoint to get the live price of BTC/USD
                response = api.query_public('Ticker', {'pair': pair, 'interval': 5})
                live_price = float(list(response['result'].values())[0]['c'][0])
                conn.execute(text(
                    f"UPDATE {coinTicker.lower()}_smaTargets SET latest_price = {live_price} WHERE date = \'{sma_date}\'"))
                conn.commit()

                # Calculate the margin away from SMA trigger price
                conn.execute(text(
                    f"UPDATE {coinTicker.lower()}_smaTargets SET margin = {round(live_price / max(short_sma, medium_sma), 3)} WHERE date = \'{sma_date}\'"))
                conn.commit()
                print(f"The live price of {coinTicker} is {live_price}")
                print(f"The SMAs for today are short = {round(short_sma, 2)} & medium = {round(medium_sma, 2)}")

                if buy_cash + coin_amount > 0:
                    # If we are not boughtIn
                    if not boughtIn:
                        # Place Market Order
                        if live_price >= order_price:
                            print(f"Placing market buy order on {coinTicker}")
                            # Calculate the maximum volume we can buy with our available cash
                            max_volume = round(buy_cash / order_price, decimals)
                            print(f"Trying to buy {max_volume} {coinTicker}")
                            retry_count = 0
                            while retry_count < 10:
                                try:
                                    response = api.query_private("AddOrder", {
                                        "pair": pair,
                                        "type": "buy",
                                        "ordertype": "market",
                                        "volume": max_volume
                                    })
                                    if response["error"]:
                                        raise Exception(response["error"])
                                    else:
                                        print("Market transaction successful!")
                                        print(response['result'])
                                        break
                                except Exception as e:
                                    print("Error making market transaction: {}".format(e))
                                    print("Retrying in 4 seconds...")
                                    time.sleep(4)
                                    retry_count += 1
                            else:
                                print("Maximum retry count reached. Unable to make market transaction.")
                        else:
                            print("Not time to buy just yet.")
                    # If we are boughtIn
                    else:
                        # Placing a market sell order
                        if live_price <= order_price:
                            print(f"Placing market sell order on {coinTicker}")
                            retry_count = 0
                            while retry_count < 10:
                                try:
                                    response = api.query_private("AddOrder", {
                                        "pair": pair,
                                        "type": "sell",
                                        "ordertype": "market",
                                        "volume": coin_amount
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
                        else:
                            print("Not time to sell just yet.")
                else:
                    print("No money invested for this coin yet.")
            else:
                print("Transaction already occurred today.")
            print("Finished\n\n--------------------\n")
