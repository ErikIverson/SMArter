DO $$
DECLARE
  coin VARCHAR(5);
BEGIN
  FOR coin IN SELECT DISTINCT coinTicker FROM smaValues LOOP
    EXECUTE 'ALTER TABLE ' || coin || '_transactions ADD COLUMN time TIME';
  END LOOP;
END $$;
