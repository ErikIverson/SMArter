DO $$
DECLARE
  coin VARCHAR(5);
BEGIN
  FOR coin IN SELECT DISTINCT coinTicker FROM smaValues
  LOOP
    EXECUTE 'DROP TABLE ' || coin || '_smaTargets';
  END LOOP;
END $$;
