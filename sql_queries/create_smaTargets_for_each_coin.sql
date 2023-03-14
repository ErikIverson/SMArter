DO $$
DECLARE
  coin VARCHAR(5);
BEGIN
  FOR coin IN SELECT DISTINCT coinTicker FROM smaValues
  LOOP
    EXECUTE 'ALTER TABLE ' || coin || '_smaTargets ADD COLUMN margin FLOAT';
    EXECUTE 'UPDATE ' || coin || '_smaTargets SET margin = latest_price / GREATEST(short, medium)';
  END LOOP;
END $$;
