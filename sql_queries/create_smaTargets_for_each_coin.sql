DO $$
DECLARE
  coin VARCHAR(5);
BEGIN
  FOR coin IN SELECT DISTINCT coinTicker FROM smaValues
  LOOP
    EXECUTE 'CREATE TABLE ' || coin || '_smaTargets (ID SERIAL PRIMARY KEY, date DATE, short FLOAT, medium FLOAT)';
  END LOOP;
END $$;
