DO $$
DECLARE
  coin VARCHAR(5);
BEGIN
  FOR coin IN SELECT DISTINCT coinTicker FROM smaValues LOOP
    EXECUTE 'CREATE TABLE ' || coin || '_transactions (
      id SERIAL PRIMARY KEY,
      date DATE,
      direction VARCHAR(4) CHECK (direction IN (''Buy'', ''Sell'')),
      fee_type VARCHAR(5) CHECK (fee_type IN (''Maker'', ''Taker'')),
      price FLOAT
    );';
  END LOOP;
END $$;
