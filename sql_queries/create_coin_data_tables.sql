DO $$
DECLARE
  coin VARCHAR(5);
BEGIN
  FOR coin IN SELECT DISTINCT coinTicker FROM smaValues LOOP
    EXECUTE 'CREATE TABLE ' || coin || '_data (
      id SERIAL PRIMARY KEY,
      date DATE,
      open FLOAT,
      high FLOAT,
      low FLOAT,
      close FLOAT
    );';
  END LOOP;
END $$;
