# Trying Real Simulation of Strategy

# Our goal is to see how SMArter Not Harder Strategy ACTUALLY would have performed
# over the last year or two and test out some different scoring functions to pick
# the ideal ones. 
# 
# Essentially, we need to pick a "start date" which will be the first day we have
# the ability to invest. Given this day, we'll use the previous 100 days to find
# the best recent SMA combination to use for the next day's evaluation. I am very
# curious to see the evolution of top SMA combos & if that volatility messes up
# the strategy at all. 
# 
# This will let us see a true simulation of how we would have done not knowing the
# future prices of any coin at any time. This script should be highly customizable
# to input a coin ticker & start date - and get a summary of performance up until the
# current day. This will be a very accurate representation of the strategy's ability
# rather than taking a mean from all possible combinations bc in reality we will only
# use one (or a handful, yet to be determined).

# 0 = 02/18/2020 for full Data Set

# First function: Calculate top SMAs based on date & return them
findSMAs_forDate <- function(investing_date, coin_ticker){
  
  #Testing
  coin_ticker = "ADA"
  investing_date = 30
  
  coin_data = read.csv(paste('./coin_data/', coin_ticker,'.csv', sep=''))
  coin_data['Prices'] = (coin_data['Low'] + coin_data['High'] + coin_data['Open'] + coin_data['Close']) / 4
  coin_data = coin_data[-c(1:26),]
  
  start_date = 1
  end_date = nrow(coin_data)
  
  print(paste("Finding Optimal SMA for period", 
              coin_data[start_date, 'Date'], "-", coin_data[end_date, 'Date']))
  
  shortSMA = c(5:12)
  midSMA = c(10:26)
  
  MAKER_FEE = 0.0016
  TAKER_FEE = 0.0026
  
  shorts = c(0)
  mids = c(0)
  dates = c('')
  leng = c(0)
  gains = c(0.1)
  trans = c(0)
  count_gains = c(0)
  count_losses = c(0)
  buy_dates = c('')
  
  final_selection = data.frame(dates, leng, gains, count_gains, count_losses, shorts, mids, trans, buy_dates)
  final_selection$gains = as.numeric(final_selection$gains)
  
  for (mid in midSMA) {
    for (short in shortSMA) {
      money = 10000
      amount = 0
      transactions = 0
      num_gains = 0
      num_losses = 0
      bought_in = FALSE
      buy_date = ''
      for (i in start_date:end_date) {
        if (bought_in == FALSE && coin_data[i, 'High'] > max(coin_data[i, short + 2], coin_data[i, mid + 2])) {
          if (max(coin_data[i, short + 2], coin_data[i, mid + 2]) > coin_data[i, 'Open']){
            amount = money / (max(coin_data[i, short + 2], coin_data[i, mid + 2])) * (1 - MAKER_FEE)
            buy_price = (max(coin_data[i, short + 2], coin_data[i, mid + 2]))
          } else {
            amount = money / (coin_data[i, 'Open']) * (1 - TAKER_FEE)
            buy_price = (coin_data[i, 'Open'])
          }
          
          # buy_price = (max(coin_data[i, short + 2], coin_data[i, mid + 2]))
          # amount = money / (max(coin_data[i, short + 2], coin_data[i, mid + 2]))

          money = 0
          bought_in = TRUE
          transactions = transactions + 1
          buy_date = paste(buy_date, coin_data[i, 'Date'], "")
        }
        else if (bought_in == TRUE && coin_data[i, 'Low'] < max(coin_data[i, short + 2], coin_data[i, mid + 2])) {
          if (max(coin_data[i, short + 2], coin_data[i, mid + 2] < coin_data['Open'])) {
            money = max(coin_data[i, short + 2], coin_data[i, mid + 2]) * amount * (1 - MAKER_FEE)
            sell_price = max(coin_data[i, short + 2], coin_data[i, mid + 2])
          } else {
            money = coin_data[i, 'Open'] * amount * (1 - TAKER_FEE)
            sell_price = coin_data[i, 'Open']
          }

          # money = max(coin_data[i, short + 2], coin_data[i, mid + 2]) * amount * (1 - MAKER_FEE)
          # sell_price = max(coin_data[i, short + 2], coin_data[i, mid + 2])
          
          if (sell_price > buy_price){num_gains = num_gains + 1} else {num_losses = num_losses + 1}
          bought_in = FALSE
          amount = 0
          transactions = transactions + 1
        }
      }
  
      gain = money + amount * coin_data[i, "Prices"]
      final_selection[nrow(final_selection) + 1,] = c(coin_data[start_date, 'Date'], end_date - start_date + 1,
                                  as.numeric(gain), num_gains, num_losses, short, mid, transactions, buy_date)
    }
  } 

  
  final_selection$gains = as.numeric(final_selection$gains)
  final_selection$count_gains = as.numeric(final_selection$count_gains)
  final_selection$count_losses = as.numeric(final_selection$count_losses)
  
  getmode <- function(v) {
    uniqv <- unique(v)
    uniqv[which.max(tabulate(match(v, uniqv)))]
  }
  
  short_Final = getmode(as.numeric(head(final_selection[rev(order(final_selection$gains)), c(3, 4, 5, 6, 7)], 50)$shorts))
  mid_Final = getmode(as.numeric(head(final_selection[rev(order(final_selection$gains)), c(3, 4, 5, 6, 7)], 50)$mids))

  print(paste("SMA Values: ", short_Final, ", ", mid_Final, sep = ''))
  return(c(short_Final, mid_Final))
}

  