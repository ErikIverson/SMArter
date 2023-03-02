import cbpro
from urllib.request import urlopen, Request

MATIC_BUY_PRICE = 1.72

api_key = '384613df61694077eba473b2c7e75589'
api_secret = 'hogx34JFQdjuo+maBdPHqbH19X1Tfw+EDllDuE42S1snkBQMcE4gnAmLy5SF/n7tx5eIzPdnNTkmn0p2l6elzw=='
api_phrase = 'EIwabswpbahalmc$19'

def readAccounts():
    liveTokens = []
    auth_client = cbpro.AuthenticatedClient(key=api_key, b64secret=api_secret, passphrase=api_phrase)
    accounts = auth_client.get_accounts()
    for acct in accounts:
        if float(acct['balance']) > 0:
            liveTokens.append({acct['currency']:{'id':acct['profile_id'],'balance':acct['balance']}})

    # for token in liveTokens:
    #     name = list(token.keys())[0]
    #     print(token[name]['id'])
    #     history = auth_client.get_account_history(token[name]['id'])
    # print(liveTokens)
    return liveTokens

def checkPrices():
    liveTokens = readAccounts()
    public_client = cbpro.PublicClient()
    for token in liveTokens:
        ticker = list(token.keys())[0]
        products = public_client.get_product_ticker(product_id=ticker + '-USD')
        price = float(products['price'])
        print("Bought at: $", MATIC_BUY_PRICE, "Current price: $", price)
        print("Percent Change", str(round(-1*(1 - price / MATIC_BUY_PRICE), 4) * 100) + '%')
        if price / MATIC_BUY_PRICE >= 1.15:
            print("Sell!")
        else:
            print('Hold on for now.')

def tryHttp():
    headers = {
    "User-Agent": 'Mozilla/5.0'
    }
    url = "https://api.pro.coinbase.com/products/BTC-USD/ticker"
    req = Request(url = url, headers = headers)
    r = urlopen(req).read()
    print(r)

if __name__ == "__main__":
    checkPrices()
    tryHttp()




