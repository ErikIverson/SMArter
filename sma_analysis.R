#### Begin 

evaluateSMA <- function(coin_ticker, start_var, end_var, START_VALUE, END_VALUE) {

  # Testing
  # start_var = "2021-12-10"
  # end_var = "2023-02-10"
  # START_VALUE = 1000
  # END_VALUE = 1148.99
  
  coin_data = read.csv(paste('./coin_data/', COIN_TICKER,'.csv', sep=''))
  coin_data = coin_data[-c(1:26),]
  coin_data['Prices'] = (coin_data['Low'] + coin_data['High'] + coin_data['Open'] + coin_data['Close']) / 4
  
  shortSMA = c(5:12)
  midSMA = c(10:26)
  
  start_date = which(coin_data$Date == start_var)
  end_date = which(coin_data$Date == end_var)
  
  shorts = c(0)
  mids = c(0)
  dates = c('')
  leng = c(0)
  gains = c(0.1)
  trans = c(0)
  buy_dates = c('')
  
  MAKER_FEE = 0.0016
  TAKER_FEE = 0.0026
  
  final_sma_analysis = data.frame(dates, leng, gains, shorts, mids, trans, buy_dates)
  final_sma_analysis$gains = as.numeric(final_sma_analysis$gains)
  
  for (mid in midSMA) {
    for (short in shortSMA) {
      money = START_VALUE
      amount = 0
      transactions = 0
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
          
          # amount = money / (max(coin_data[i, short + 2], coin_data[i, mid + 2])) * (1 - MAKER_FEE)
          # buy_price = (max(coin_data[i, short + 2], coin_data[i, mid + 2]))

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

          
          bought_in = FALSE
          amount = 0
          transactions = transactions + 1
        }
      }
        
      gain = money + amount * sell_price
      final_sma_analysis[nrow(final_sma_analysis) + 1,] = c(coin_data[start_date, 'Date'], end_date - start_date + 1,
                                  as.numeric(gain), short, mid, transactions, buy_date)
    }
    final_sma_analysis$gains = as.numeric(final_sma_analysis$gains)
  }
  print(paste("Gains possible: $", round(final_sma_analysis[which.max(final_sma_analysis$gains),]$gains, 2), sep = ""))
  return (100 * sum(final_sma_analysis$gains < END_VALUE) / length(final_sma_analysis$gains))
}

