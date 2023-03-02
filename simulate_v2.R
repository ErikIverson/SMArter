rm(list = ls())
setwd("C:/Users/eriki/Desktop/Crypto")
source("./findSMA_forDate.R")
source("./sma_analysis.R")
source("./visualizations.R")

# Set Variables:

COIN_TICKER = "ETH"

{
  START_AT = "2020-04-01"
  END_AT = "2023-02-11"
  
  START_VALUE = 1000
  
  shortSMA = 9
  midSMA = 24
  
  short_previous = 0
  mid_previous = 0 
  # Calculate SMA & Import Coin Data
  {
    live_prices = read.csv(paste('./coin_data_hourly/', COIN_TICKER, '.csv', sep=''))
    sma_prices =  read.csv(paste('./coin_data/', COIN_TICKER, '-SMAs.csv', sep=''))
    
    MAKER_FEE = 0.0016
    TAKER_FEE = 0.0026
    
    # For tracking how many SMA buys/sells vs market buys/sells
    smaBuys = 0
    smaSells = 0
    marketBuys = 0
    marketSells = 0
    
    hour_interval = 36
    temp_interval = hour_interval
    override_threshold = 0.025
  }
  
  
  # Initialize Ledger Book
  {
    ledger = data.frame("Date"=c(live_prices[1, 'Date']),
                        "Action"=c('Start'),
                        "Money"=c(START_VALUE),
                        "Amount"=c(0),
                        "Price"=c(live_prices[1, 'Open']),
                        "total_fees"=c(0),
                        "iteration"=c(0))
    
    # Starting Vars
    money = START_VALUE
    amount = 0
    transactions = 0
    transaction_costs = 0
    bought_in = FALSE
    buy_date = ''
  }
  
  # Simulation Begins
  for (i in seq(2184, nrow(live_prices), 1)){
    short = sma_prices[which(sma_prices$Date == strsplit(live_prices[i, 'Date'], " ")[[1]][1]), shortSMA + 2]
    mid   = sma_prices[which(sma_prices$Date == strsplit(live_prices[i, 'Date'], " ")[[1]][1]), midSMA + 2]
    
    # short = sma_prices[which(sma_prices$Date == live_prices[i, 'Date']), shortSMA + 2]
    # mid   = sma_prices[which(sma_prices$Date == live_prices[i, 'Date']), midSMA + 2]
    
    if (nrow(live_prices) - i < hour_interval) {temp_interval = nrow(live_prices) - i}
    
    if ((i %% hour_interval) == 0) {
      if (bought_in == FALSE && any(live_prices[i:(i+temp_interval), 'High'] > max(short, mid))) {
        
        if (max(short, mid) > live_prices[i, 'Open']){
          buy_price = max(short, mid)
          amount = money / buy_price * (1 - MAKER_FEE)
          transaction_costs = transaction_costs + (money * (MAKER_FEE))
          smaBuys = smaBuys + 1
          print(paste("SMA buy price:", buy_price))
          print(paste("Date:", live_prices[i, 'Date']))
        } 
        else {
          buy_price = live_prices[i, 'Open']
          amount = money / buy_price * (1 - TAKER_FEE)
          transaction_costs = transaction_costs + (money * (TAKER_FEE))
          marketBuys = marketBuys + 1
          print(paste("Market buy price:", buy_price))
          print(paste("$", buy_price - max(short, mid), "higher than SMA"))
          print(paste("Date:", live_prices[i, 'Date']))
        }
        
        money = 0
        bought_in = TRUE
        transactions = transactions + 1
        ledger[nrow(ledger)+1,] = c(live_prices[i, 'Date'], "BUY", money, amount, buy_price, transaction_costs, i)
      }
      else if (bought_in == TRUE && any(live_prices[i:(i+temp_interval), 'Low'] < max(short, mid))) {
        
        if (max(short, mid) < live_prices[i, 'Open']) {
          sell_price = max(short, mid)
          money = sell_price * amount * (1 - MAKER_FEE)
          transaction_costs = transaction_costs + (sell_price * amount * (MAKER_FEE))
          print(paste("SMA Sell Date:", live_prices[i, 'Date']))
          smaSells = smaSells + 1
        } 
        else {
          sell_price = live_prices[i, 'Open']
          money = sell_price * amount * (1 - TAKER_FEE)
          transaction_costs = transaction_costs + (sell_price * amount * (TAKER_FEE))
          marketSells = marketSells + 1
          print(paste("Market Sell Date:", live_prices[i, 'Date']))
        }
        
        bought_in = FALSE
        amount = 0
        transactions = transactions + 1
        
        ledger[nrow(ledger)+1,] = c(live_prices[i, 'Date'], "SELL", money, amount, sell_price, transaction_costs, i)
      }
    } else {
      
      if (bought_in == TRUE && live_prices[i, 'Open'] < max(short, mid) &&
            (live_prices[i, 'Open'] / mean(live_prices[(i-ifelse(i>12, 12, i)):i, 'Open']) < (1 - 0.02))){
        sell_price = live_prices[i, 'Open']
        money = sell_price * amount * (1 - TAKER_FEE)
        transaction_costs = transaction_costs + (sell_price * amount * (TAKER_FEE))
        print(paste("Override sell price:", sell_price))
        print(paste("$", max(short, mid) - sell_price, "lower than SMA"))
        print(paste("Date:", live_prices[i, 'Date']))

        bought_in = FALSE
        amount = 0
        transactions = transactions + 1
        ledger[nrow(ledger)+1,] = c(live_prices[i, 'Date'], "SELL", money, amount, sell_price, transaction_costs, i)
      }
      else if (bought_in == FALSE && live_prices[i, 'Open'] > max(short, mid) &&
            (live_prices[i, 'Open'] / mean(live_prices[(i-ifelse(i>24, 24, i)):i, 'Open']) > (1 + 0.04))){
        buy_price = live_prices[i, 'Open']
        amount = money / buy_price * (1 - TAKER_FEE)
        transaction_costs = transaction_costs + (money * (TAKER_FEE))
        marketBuys = marketBuys + 1
        print(paste("Override buy price:", buy_price))
        print(paste("$", buy_price - max(short, mid), "higher than SMA"))
        print(paste("Date:", live_prices[i, 'Date']))

        money = 0
        bought_in = TRUE
        transactions = transactions + 1
        ledger[nrow(ledger)+1,] = c(live_prices[i, 'Date'], "BUY", money, amount, buy_price, transaction_costs, i)
      }
    }
  }
  total_gains = round(as.numeric(ledger[nrow(ledger),]$Money), 2)
  total_gains = ifelse(total_gains==0, as.numeric(ledger[nrow(ledger),]$Price)*as.numeric(ledger[nrow(ledger),]$Amount), total_gains)
  print(paste("Final Balance: $", round(total_gains, 2), sep = ""))
  # print(paste("SMA Combination: ", round(evaluateSMA(COIN_TICKER, START_AT, END_AT,
  #                                                    START_VALUE, total_gains), 2), "th Percentile", sep = ""))
  print(paste("Total Fees Paid: $", ledger[nrow(ledger),]$total_fees))
  plot_performance(live_prices, ledger, 1, nrow(live_prices), shortSMA, midSMA)
  # simulation_data = data.frame(date = coin_data[INVESTMENT_DATE:END_TIME,]$Date, avg_price = coin_data[INVESTMENT_DATE:END_TIME,]$Prices, 
  #                              high = coin_data[INVESTMENT_DATE:END_TIME,]$High,
  #                              low = coin_data[INVESTMENT_DATE:END_TIME,]$Low,
  #                              open = coin_data[INVESTMENT_DATE:END_TIME,]$Open,
  #                              close = coin_data[INVESTMENT_DATE:END_TIME,]$Close)
}

