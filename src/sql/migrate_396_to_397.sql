--
-- Make the changes needed to move from v3.9.6 to 3.9.7
-- This is just the SQL changes, the application will need to run some logic
-- too. Use the "oasisdb" tool to run this, do not try to run it directly.
--

SET statement_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;

BEGIN;

update config SET "value" = '3.9.7' WHERE "name" = 'dbversion';

-- store the attribute we use to map LTI to OASIS usernames.
ALTER TABLE lti_consumers ADD COLUMN "username_attribute" character varying default 'name';

COMMIT;