CREATE TABLE coinBalances (
  ID SERIAL PRIMARY KEY,
  coinTicker VARCHAR(5) UNIQUE,
  boughtIn BOOLEAN,
  usdc FLOAT,
  coinAmount FLOAT,
  totalInvested FLOAT,
  totalFees FLOAT,
  newInvestments FLOAT,
  netGains FLOAT,
  netMultiplier FLOAT
);
