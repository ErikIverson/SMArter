rm(list =ls())

# A place to gather the SMA simulator data separately & save to CSV
source("./findSMA_forDate.R")

smaDF = data.frame("Date"= c(''), "short"=c(0),"mid"=c(0), "long"=c(0))

COIN_TICKER = "ETH"
INVESTMENT_DATE = 51
LENGTH_OF_TIME = 990
LAG = 50

coin_data = read.csv(paste('./coin_data/', COIN_TICKER,'.csv', sep=''))
coin_data['Prices'] = (coin_data['Open'] + coin_data['High'] + coin_data['Low'] + coin_data['Close']) / 4
coin_data = coin_data[-c(1:50),]

# Getting optimal SMA for last 50 days
{
  for (i in c(INVESTMENT_DATE:(INVESTMENT_DATE+LENGTH_OF_TIME))){
    print(i)
    smas = findSMAs_forDate(i, COIN_TICKER, LAG)
    print(smas)
    if (i == INVESTMENT_DATE) {
      smaDF[nrow(smaDF),] = c(coin_data[i, 'Date'], smas[1], smas[2], smas[3]) 
    } else {
      smaDF[nrow(smaDF)+1,] = c(coin_data[i, 'Date'], smas[1], smas[2], smas[3]) 
    }
  }
  write.csv(smaDF, "ETH_FullLag50_optimal_SMAs.csv")
}





