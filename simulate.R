rm(list = ls())
setwd("C:/Users/eriki/Desktop/Crypto")
source("./findSMA_forDate.R")
source("./sma_analysis.R")
source("./visualizations.R")

# Set Variables:

COIN_TICKER = "DOT"

{
  # START_AT = "2/11/2022"
  # END_AT = "2/12/2023"
  START_AT = "2021-10-26"
  END_AT = "2023-02-16"

  START_VALUE = 1000

  # Calculate SMA & Import Coin Data
  {
    coin_data = read.csv(paste('./coin_data/', COIN_TICKER,'.csv', sep=''))
    coin_data['Prices'] = (coin_data['Low'] + coin_data['High'] + coin_data['Open'] + coin_data['Close']) / 4
    #coin_data = coin_data[-c(1:26),]

    END_TIME = which(coin_data$Date == END_AT)
    
    INVESTMENT_DATE = which(coin_data$Date == START_AT)
    
    MAKER_FEE = 0.0016
    TAKER_FEE = 0.0026
    
    SMAvector = findSMAs_forDate(INVESTMENT_DATE, COIN_TICKER)
    short = 7#SMAvector[1]
    mid = 26#SMAvector[2]
    
    # For tracking how many SMA buys/sells vs market buys/sells
    smaBuys = 0
    smaSells = 0
    marketBuys = 0
    marketSells = 0
  }
  
  
  # Initialize Ledger Book
  {
    ledger = data.frame("Date"=c(coin_data[INVESTMENT_DATE, 'Date']),
                        "Action"=c('Start'),
                        "Money"=c(START_VALUE),
                        "Amount"=c(0),
                        "Price"=c(coin_data[INVESTMENT_DATE, 'Prices']),
                        "total_fees"=c(0))
    
    # Starting Vars
    money = START_VALUE
    amount = 0
    transactions = 0
    transaction_costs = 0
    bought_in = FALSE
    buy_date = ''
  }
  
  # Simulation Begins
  for (i in c(INVESTMENT_DATE:(END_TIME))){
    
    if (bought_in == FALSE && coin_data[i, 'High'] > max(coin_data[i, short + 2], coin_data[i, mid + 2])) {

      if (max(coin_data[i, short + 2], coin_data[i, mid + 2]) > coin_data[i, 'Open']){
        amount = money / (max(coin_data[i, short + 2], coin_data[i, mid + 2])) * (1 - MAKER_FEE)
        buy_price = (max(coin_data[i, short + 2], coin_data[i, mid + 2]))
        transaction_costs = transaction_costs + (money * (MAKER_FEE))
        smaBuys = smaBuys + 1
      } else {
        buy_price = coin_data[i, 'Open'] 
        amount = money / buy_price * (1 - TAKER_FEE)
        transaction_costs = transaction_costs + (money * TAKER_FEE)
        marketBuys = marketBuys + 1
        print(paste("Market buy on:", coin_data[i, 'Date']))
      }
      
      money = 0
      bought_in = TRUE
      transactions = transactions + 1
      
      ledger[nrow(ledger)+1,] = c(coin_data[i, 'Date'], "BUY", money, amount, buy_price, transaction_costs)
    }
    else if (bought_in == TRUE && coin_data[i, 'Low'] < max(coin_data[i, short + 2], coin_data[i, mid + 2])) {
      
      if (max(coin_data[i, short + 2], coin_data[i, mid + 2] < coin_data['Open'])) {
        sell_price = max(coin_data[i, short + 2], coin_data[i, mid + 2])
        money = sell_price * amount * (1 - MAKER_FEE)
        transaction_costs = transaction_costs + (sell_price * amount * (MAKER_FEE))
        smaSells = smaSells + 1
        print(paste("Sold on:", coin_data[i, 'Date']))
      } else {
        sell_price = coin_data[i, 'Open']
        money = sell_price * amount * (1 - TAKER_FEE)
        transaction_costs = transaction_costs + (sell_price * amount * TAKER_FEE)
        # sell_price = max(coin_data[i-1, short + 2], coin_data[i-1, mid + 2])
        marketSells = marketSells + 1
      }
      
      bought_in = FALSE
      amount = 0
      transactions = transactions + 1
      
      ledger[nrow(ledger)+1,] = c(coin_data[i, 'Date'], "SELL", money, amount, sell_price, transaction_costs)
      
    }
  }
  total_gains = round(as.numeric(ledger[nrow(ledger),]$Money), 2)
  total_gains = ifelse(total_gains==0, as.numeric(ledger[nrow(ledger),]$Price)*as.numeric(ledger[nrow(ledger),]$Amount), total_gains)
  print(paste("Final Balance: $", round(total_gains, 2), sep = ""))
  print(paste("SMA Combination: ", round(evaluateSMA(COIN_TICKER, START_AT, END_AT,
        START_VALUE, total_gains), 2), "th Percentile", sep = ""))
  print(paste("Total Fees Paid: $", ledger[nrow(ledger),]$total_fees))
  plot_performance(coin_data, ledger, INVESTMENT_DATE, END_TIME, short, mid)
  simulation_data = data.frame(date = coin_data[INVESTMENT_DATE:END_TIME,]$Date, avg_price = coin_data[INVESTMENT_DATE:END_TIME,]$Prices, 
                               high = coin_data[INVESTMENT_DATE:END_TIME,]$High,
                               low = coin_data[INVESTMENT_DATE:END_TIME,]$Low,
                               open = coin_data[INVESTMENT_DATE:END_TIME,]$Open,
                               close = coin_data[INVESTMENT_DATE:END_TIME,]$Close)
}

