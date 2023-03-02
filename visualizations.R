library(ggplot2)

plot_performance <- function(coin_data, ledger, INVESTMENT_DATE, END_TIME, short, mid) {
  # Load the data into a data frame
  print("entering plots")
  df_CoinData <- data.frame(date = as.Date(coin_data[INVESTMENT_DATE:END_TIME,]$Date),
                   price = coin_data[INVESTMENT_DATE:END_TIME,]$Open)
  ("entering plots 8")
  df_CoinData_Highs <- data.frame(date = as.Date(coin_data[INVESTMENT_DATE:END_TIME,]$Date),
                       price = coin_data[INVESTMENT_DATE:END_TIME,]$High)
  ("entering plots 11")
  df_CoinData_Lows <- data.frame(date = as.Date(coin_data[INVESTMENT_DATE:END_TIME,]$Date),
                        price = coin_data[INVESTMENT_DATE:END_TIME,]$Low)
  # short_data = data.frame(date = as.Date(coin_data[INVESTMENT_DATE:END_TIME,]$Date),
  #                      price = as.numeric(coin_data[INVESTMENT_DATE:END_TIME, short+2]))
  # mid_data = data.frame(date = as.Date(coin_data[INVESTMENT_DATE:END_TIME,]$Date),
  #                      price = as.numeric(coin_data[INVESTMENT_DATE:END_TIME, mid+2]))

  df_Buys <- data.frame(date = as.Date(ledger[which(ledger$Action=="BUY"),]$Date),
                        price = as.numeric(ledger[which(ledger$Action=="BUY"),]$Price))
  ("entering plots21")
  df_Sells <- data.frame(date = as.Date(ledger[which(ledger$Action=="SELL"),]$Date),
                         price = as.numeric(ledger[which(ledger$Action=="SELL"),]$Price))
  df_Ledger <- data.frame(date = as.Date(ledger$Date),
                         price = as.numeric(ledger$Price))
  # df_CoinData_small <- data.frame(date = as.Date(coin_data[INVESTMENT_DATE:END_TIME,]$Date),
  #                           price = short_data)
  # df_CoinData_medium <- data.frame(date = as.Date(coin_data[INVESTMENT_DATE:END_TIME,]$Date),
  #                           price = mid_data)
  # Plot the data
  
  myplot <- ggplot() +
    geom_line(data = df_CoinData, aes(x = date, y = price), color = "blue", size = 0.2) +
    geom_line(data = df_CoinData_Lows, aes(x = date, y = price), size = .15) +
    geom_line(data = df_CoinData_Highs, aes(x = date, y = price), size = .15) +
    # geom_line(data = short_data, aes(x = date, y = price), size = .4) +
    # geom_line(data = mid_data, aes(x = date, y = price), size = .4) +
    geom_point(data = df_Buys, aes(x = date, y = price), shape = "o", size = .3) +
    geom_point(data = df_Sells, aes(x = date, y = price), shape = "o", size = .3) +
    xlab("Date") +
    ylab("Price") +
    # theme(panel.grid.minor.x = element_line(margin(1))) +
    ggtitle("Coin Data Over Time")

  # Create mini buy/sell dfs
  for (i in seq(2, nrow(ledger), by = 2)){
    newVariable = paste("df_trans", i, sep='')
    value = data.frame(date = as.Date(ledger[i:(i+1), 'Date']), price = as.numeric(ledger[i:(i+1), 'Price']))
    assign(newVariable, value)
    myplot <- myplot + geom_line(data = data.frame(date = as.Date(ledger[i:(i+1), 'Date']), price = as.numeric(ledger[i:(i+1), 'Price'])),
                       aes(x = date, y = price), color =
                         ifelse(as.numeric(ledger[i+1,]$Price) > as.numeric(ledger[i,]$Price), "green", "red"), size = 0.1)
  }
  myplot
  
  # Save the ggplot to a PDF file
  ggsave("plot.pdf", myplot)
  
  # Open the PDF file in a separate window using the command line
  system("open plot.pdf")
}

  
  
  
  
  
