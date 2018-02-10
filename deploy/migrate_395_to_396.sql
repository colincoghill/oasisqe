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

-- record when we last saw the user, so we can do things like disabling old accounts
ALTER TABLE users ADD COLUMN "last_seen" timestamp with time zone;

-- store the user's 'fullname' separately.
ALTER TABLE users ADD COLUMN "display_name" character varying;

-- keep track of LTI consumers
CREATE TABLE lti_consumers (
    "id" SERIAL PRIMARY KEY,
    "title" character varying(250),
    "shared_secret" character varying,
    "consumer_key" character varying,
    "comments" character varying,
    "active" BOOLEAN default FALSE,
    "last_seen" timestamp with time ZONE
);

-- LTI parameters at a course level
CREATE TABLE lti_course_params (
    "course_id" INTEGER,
    "lti_enabled" BOOLEAN default FALSE,
    "lti_consumer" INTEGER,
    "lti_coursename" CHARACTER VARYING,
    "lti_auto_add_user" BOOLEAN default FALSE,
    "lti_instructor_access" BOOLEAN default FALSE
);
CREATE INDEX lti_consumers_consumer_key ON lti_consumers USING btree (consumer_key);

COMMIT;