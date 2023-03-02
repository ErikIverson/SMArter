CREATE TABLE coinBalances (
  ID SERIAL PRIMARY KEY,
  coinTicker VARCHAR(5) UNIQUE,
  boughtIn BOOLEAN,
  investments FLOAT,
  money FLOAT,
  amount FLOAT
);
