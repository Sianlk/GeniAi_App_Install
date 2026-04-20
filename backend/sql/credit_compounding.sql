-- Requires pg_cron extension in PostgreSQL
CREATE EXTENSION IF NOT EXISTS pg_cron;

CREATE OR REPLACE FUNCTION apply_monthly_credit_compound()
RETURNS void
LANGUAGE plpgsql
AS $$
DECLARE
  rec RECORD;
  bonus BIGINT;
BEGIN
  FOR rec IN SELECT id, credits_pence FROM "User" LOOP
    IF rec.credits_pence > 0 THEN
      bonus := FLOOR(rec.credits_pence * 0.05);

      UPDATE "User"
      SET credits_pence = credits_pence + bonus,
          "updatedAt" = NOW()
      WHERE id = rec.id;

      INSERT INTO "CreditTxn"(id, "userId", type, "amountPence", currency, meta, "createdAt")
      VALUES (gen_random_uuid(), rec.id, 'COMPOUND_REWARD', bonus, 'GBP',
        jsonb_build_object('rate', 0.05, 'kind', 'monthly_compound'), NOW());
    END IF;
  END LOOP;
END;
$$;

SELECT cron.schedule(
  'monthly-credit-compound',
  '0 0 1 * *',
  $$SELECT apply_monthly_credit_compound();$$
);
