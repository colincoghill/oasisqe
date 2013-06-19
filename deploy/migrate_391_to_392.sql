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



-- OLD
CREATE TABLE courses (
    course integer DEFAULT nextval('courses_course_seq'::regclass) NOT NULL,
    title character varying(128) NOT NULL,
    description text,
    owner integer,
    active integer DEFAULT 1,
    "type" integer,
    enrol_type character varying DEFAULT 'manual'::character varying,
    enrol_location character varying,
    enrol_freq integer DEFAULT 120,
    registration character varying DEFAULT 'controlled'::character varying,
    practice_visibility character varying DEFAULT 'all'::character varying,
    assess_visibility character varying DEFAULT 'enrol'::character varying
);
-- NEW
CREATE TABLE courses (
    "course" SERIAL PRIMARY KEY,
    "title" character varying(128) NOT NULL,
    "description" text,
    "owner" integer,
    "active" integer DEFAULT 1,
    "type" integer,
    "practice_visibility" character varying DEFAULT 'all'::character varying,
    "assess_visibility" character varying DEFAULT 'enrol'::character varying
);



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

CREATE TABLE grouptypes (
    "type" SERIAL PRIMARY KEY,
    "title" character varying(128) NOT NULL,
    "description" text
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




-- OLD
CREATE TABLE groupcourses (
    id integer DEFAULT nextval('groupcourses_id_seq'::regclass) NOT NULL,
    groupid integer NOT NULL,
    active integer DEFAULT 0,
    course integer NOT NULL
);
-- NEW
CREATE TABLE groupcourses (
    "id" SERIAL PRIMARY KEY,
    "groupid" integer REFERENCES ugroups("id") NOT NULL,
    "course" integer REFERENCES courses("course")NOT NULL
);




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



-- OLD
CREATE TABLE permissions (
    id integer DEFAULT nextval('permissions_id_seq'::regclass) NOT NULL,
    course integer NOT NULL,
    userid integer NOT NULL,
    permission integer
);
-- NEW
CREATE TABLE permissions (
    "id" SERIAL PRIMARY KEY,
    "course" integer NOT NULL,
    "userid" integer references users("id"),
    "permission" integer REFERENCES permissiondesc("permission")
);




-- OLD
CREATE TABLE stats_prac_q_course (
    qtemplate integer NOT NULL,
    "when" timestamp with time zone,
    hour integer NOT NULL,
    day integer NOT NULL,
    month integer NOT NULL,
    year integer NOT NULL,
    "number" integer NOT NULL
);
-- NEW
CREATE TABLE stats_prac_q_course (
    qtemplate integer NOT NULL,
    "when" timestamp with time zone,
    "hour" integer NOT NULL,
    "day" integer NOT NULL,
    "month" integer NOT NULL,
    "year" integer NOT NULL,
    "number" integer NULL,
    "avgscore" float NULL
);






-- OLD
CREATE TABLE usergroups (
    id integer DEFAULT nextval('usergroups_id_seq'::regclass) NOT NULL,
    userid integer NOT NULL,
    groupid integer NOT NULL,
    "type" integer,
    semester character varying
);
-- NEW
CREATE TABLE usergroups (
    "id" SERIAL PRIMARY KEY,
    "userid" integer REFERENCES users("id") NOT NULL,
    "groupid" integer REFERENCES ugroups("id") NOT NULL
);





CREATE TABLE config (
    "name" character varying(50) unique primary key,
    "value" text
);
INSERT INTO config ("name", "value") VALUES ('dbversion', '3.9.2');

