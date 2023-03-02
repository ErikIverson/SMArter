import cbpro
import psycopg2
from datetime import datetime, timedelta

# set the time to 9am central time
central_time_zone_offset = timedelta(hours=-6)
nine_am_central = datetime.now() + central_time_zone_offset
nine_am_central = nine_am_central.replace(hour=9, minute=0, second=0, microsecond=0)

# calculate the number of hours since the last 9am central time
now = datetime.now()
delta_since_last_nine_am = now - nine_am_central
hours_since_last_nine_am = delta_since_last_nine_am.days * 24 + delta_since_last_nine_am.seconds // 3600

# connect to the database
conn = psycopg2.connect(
    host="sma-v1beta.ckdrjttqqkf8.us-east-2.rds.amazonaws.com",
    database="postgres",
    user="postgres",
    password="Redwings#19",
    port="5432"
)

# create a cursor
cur = conn.cursor()

# fetch coinTickers and their SMA values from the smaValues table
cur.execute("SELECT coinTicker, short, medium FROM smaValues")
sma_values = cur.fetchall()

# loop through each coinTicker and calculate the short and medium SMAs
for sma in sma_values:
    coin_ticker = sma[0]
    short_sma_period = sma[1]
    medium_sma_period = sma[2]
    # fetch the price data for the past 25 days plus the current day
    public_client = cbpro.PublicClient()
    price_data = public_client.get_product_historic_rates(f'{coin_ticker}-USD', granularity=86400, end=now.isoformat(), start=(now - timedelta(days=25)).isoformat())

    # calculate the short and medium SMAs
    short_sma = sum(data[3] for data in price_data[-short_sma_period:]) / short_sma_period
    medium_sma = sum(data[3] for data in price_data[-medium_sma_period:]) / medium_sma_period

    # insert the SMAs into the database with the current timestamp
    cur.execute(f"INSERT INTO {coin_ticker.lower()}_smaTargets (date, short, medium) VALUES (NOW(), %s, %s)", (short_sma, medium_sma))
    conn.commit()

# close the cursor and connection
cur.close()
conn.close()
