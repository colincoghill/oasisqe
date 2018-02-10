--
-- Make the changes needed to move from v3.9.5 to 3.9.6
-- This is just the SQL changes, the application will need to run some logic
-- too. Use the "oasisdb" tool to run this, do not try to run it directly.
--

SET statement_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;



-- Put this into logic:  INSERT INTO users (uname, passwd, givenname, source, confirmed)
--       VALUES ('admin', '-NOLOGIN-', 'Admin', 'local', TRUE);

BEGIN;

update config SET "value" = '3.9.6' WHERE "name" = 'dbversion';

-- take username max length away
ALTER TABLE users ALTER COLUMN "uname" TYPE character varying;


-- keep track of LTI consumers
CREATE TABLE lti_consumers (
    "id" SERIAL PRIMARY KEY,
    "short_name" character varying(20) unique NOT NULL,
    "title" character varying(250),
    "shared_secret" character varying,
    "consumer_key" character varying,
    "comments" character varying,
    "active" BOOLEAN default FALSE,
    "lastseen" timestamp with time ZONE
);


CREATE INDEX lti_consumers_shortname ON lti_consumers USING btree (short_name);
CREATE INDEX lti_consumers_consumer_key ON lti_consumers USING btree (consumer_key);

COMMIT;