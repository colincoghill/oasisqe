--
-- Make the changes needed to move from v3.9.4 to 3.9.5
-- This is just the SQL changes, the application will need to run some logic
-- too. Use the "oasisdb" tool to run this, do not try to run it directly.
--

SET statement_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;



-- Put this into logic:  INSERT INTO users (uname, passwd, givenname, source, confirmed)
--       VALUES ('admin', '-NOLOGIN-', 'Admin', 'local', TRUE);

BEGIN;

update config SET "value" = '3.9.5' WHERE "name" = 'dbversion';

COMMIT;