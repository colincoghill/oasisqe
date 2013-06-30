--
-- Make the changes needed to move from v3.9.1 to 3.9.2
-- This is just the SQL changes, the application will need to run some logic
-- too. Use the "oasisdb" tool to run this, do not try to run it directly.
--

SET statement_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;




-- Put this into logic:  INSERT INTO users (uname, passwd, givenname, source, confirmed)
--       VALUES ('admin', '-NOLOGIN-', 'Admin', 'local', TRUE);

BEGIN;

ALTER TABLE courses DROP COLUMN "enrol_type";
ALTER TABLE courses DROP COLUMN "enrol_location";
ALTER TABLE courses DROP COLUMN "enrol_freq";
ALTER TABLE courses DROP COLUMN "registration";

CREATE TABLE periods (
    "id" SERIAL PRIMARY KEY,
    "name" character varying(50) UNIQUE NOT NULL,
    "title" character varying(250),
    "start" date,
    "finish" date,
    "code" character varying(50) unique
);

INSERT INTO periods ("name", "title", "start", "finish", "code")
             VALUES ('Indefinite', 'Indefinite', '2000-01-01', '9999-12-31','');
CREATE INDEX ON "periods" USING BTREE("name");
CREATE INDEX ON "periods" USING BTREE("code");


CREATE TABLE feeds (
    "id" SERIAL PRIMARY KEY,
    "name" character varying UNIQUE,
    "title" character varying,
    "script" character varying,
    "envvar" character varying,
    "freq" integer default 2,   -- 1 = hourly, 2 = daily, 3 = manually
    "comments" text,
    "status" character varying,
    "error" character varying,
    "active" boolean default False
);

INSERT INTO grouptypes ("type", "title", "description")
  VALUES ('1', 'staff', 'Staff');
INSERT INTO grouptypes ("type", "title", "description")
  VALUES ('2', 'enrolment', 'Enrolment');
INSERT INTO grouptypes ("type", "title", "description")
  VALUES ('3', 'statistical', 'Statistical');
SELECT SETVAL('grouptypes_type_seq', 3);

CREATE TABLE ugroups (
    "id" SERIAL PRIMARY KEY,
    "name" character varying UNIQUE,
    "title" character varying,
    "gtype" integer references grouptypes("type"),
    "source" character varying DEFAULT 'adhoc'::character varying,
    "feed" integer references feeds("id") NULL,
    "period" integer references periods("id"),
    "feedargs" character varying DEFAULT '',
    "active" boolean default TRUE
);



CREATE TABLE userfeeds (
    "id" SERIAL PRIMARY KEY,
    "name" character varying UNIQUE,
    "title" character varying,
    "script" character varying,
    "envvar" character varying,
    "freq" integer default 2,   -- 1 = hourly, 2 = daily, 3 = manually
    "comments" text,
    "priority" integer default 3,
    "regex" character varying,
    "status" character varying,
    "error" character varying,
    "active" boolean default False
);


ALTER TABLE groupcourses DROP COLUMN "active";
ALTER TABLE groupcourses ADD FOREIGN KEY("groupid") REFERENCES ugroups("id");
ALTER TABLE groupcourses ADD FOREIGN KEY("course") REFERENCES courses("course");

ALTER TABLE permissiondesc ALTER COLUMN "permission" SET NOT NULL;
ALTER TABLE permissiondesc ADD UNIQUE("permission");

INSERT INTO permissiondesc ("permission", "name", "description", "sharable")
       VALUES (1, 'sysadmin', 'System Administrator', TRUE);
INSERT INTO permissiondesc ("permission", "name", "description", "sharable")
       VALUES (2, 'useradmin', 'User Administrator', TRUE);
INSERT INTO permissiondesc ("permission", "name", "description", "sharable")
       VALUES (3, 'courseadmin', 'Course Administrator', TRUE);
INSERT INTO permissiondesc ("permission", "name", "description", "sharable")
       VALUES (4, 'coursecoord', 'Course Coordinator', TRUE);
INSERT INTO permissiondesc ("permission", "name", "description", "sharable")
       VALUES (5, 'questionedit', 'Question Editor', TRUE);
INSERT INTO permissiondesc ("permission", "name", "description", "sharable")
       VALUES (8, 'viewmarks', 'View Marks', TRUE);
INSERT INTO permissiondesc ("permission", "name", "description", "sharable")
       VALUES (9, 'altermarks', 'Alter Marks',TRUE);
INSERT INTO permissiondesc ("permission", "name", "description", "sharable")
       VALUES (10, 'questionpreview', 'Preview Practice',TRUE);
INSERT INTO permissiondesc ("permission", "name", "description", "sharable")
       VALUES (11, 'exampreview', 'Preview Assessments',TRUE);
INSERT INTO permissiondesc ("permission", "name", "description", "sharable")
       VALUES (14, 'examcreate', 'Create Assessments',TRUE);
INSERT INTO permissiondesc ("permission", "name", "description", "sharable")
       VALUES (15, 'memberview', 'View Group Members',TRUE);
INSERT INTO permissiondesc ("permission", "name", "description", "sharable")
       VALUES (16, 'surveypreview', 'Preview Surveys',TRUE);
INSERT INTO permissiondesc ("permission", "name", "description", "sharable")
       VALUES (17, 'surveycreate', 'Create Surveys',TRUE);
INSERT INTO permissiondesc ("permission", "name", "description", "sharable")
       VALUES (18, 'sysmesg', 'Set System Messages',TRUE);
INSERT INTO permissiondesc ("permission", "name", "description", "sharable")
       VALUES (19, 'syscourses', 'Add/Remove Courses',TRUE);
INSERT INTO permissiondesc ("permission", "name", "description", "sharable")
       VALUES (20, 'surveyresults', 'View Survey Results',TRUE);

SELECT setval('permissiondesc_permission_seq', 21);


ALTER TABLE permissions ADD FOREIGN KEY("userid") REFERENCES users("id");
ALTER TABLE permissions ADD FOREIGN KEY("permission") REFERENCES permissiondesc("permission");


ALTER TABLE stats_prac_q_course ADD COLUMN "avgscore" float NULL;




ALTER TABLE usergroups ADD FOREIGN KEY("userid") REFERENCES users("id");
ALTER TABLE usergroups ADD FOREIGN KEY("groupid") REFERENCES ugroups("id");
ALTER TABLE usergroups DROP COLUMN "type";
ALTER TABLE usergroups DROP COLUMN "semester";


CREATE TABLE config (
    "name" character varying(50) unique primary key,
    "value" text
);
INSERT INTO config ("name", "value") VALUES ('dbversion', '3.9.2');



COMMIT;