--
-- PostgreSQL database dump
--

SET statement_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;

CREATE TABLE audit (
    "id" SERIAL PRIMARY KEY,
    "time" timestamp without time zone,
    "class" integer DEFAULT 1,
    "instigator" integer DEFAULT 0,
    "object" integer DEFAULT 0,
    "module" character varying(200),
    "message" character varying(250),
    "longmesg" text
);

CREATE TABLE users (
    "id" SERIAL PRIMARY KEY,
    "uname" character varying(12),
    "passwd" character varying(250),
    "givenname" character varying(80),
    "familyname" character varying(80),
    "student_id" character varying(20),
    "acctstatus" integer,
    "email" character varying,
    "source" character varying,
    "expiry" timestamp ,
    "confirmation_code" character varying,
    "confirmed" character varying
);

INSERT INTO users (uname, passwd, givenname, source, confirmed)
       VALUES ('admin', '-NOLOGIN-', 'Admin', 'local', TRUE);

CREATE TABLE qtemplates (
    "qtemplate" SERIAL PRIMARY KEY,
    "owner" integer REFERENCES users("id") NOT NULL,
    "title" character varying(128) NOT NULL,
    "description" text,
    "marker" integer,
    "scoremax" real,
    "version" integer,
    "status" integer,
    "embed_id" character varying(16)
);

CREATE TABLE questions (
    "question" SERIAL PRIMARY KEY,
    "qtemplate" integer REFERENCES qtemplates("qtemplate"),
    "status" integer,
    "name" character varying(200),
    "student" integer REFERENCES users("id"),
    "score" real DEFAULT 0,
    "firstview" timestamp,
    "marktime" timestamp,
    "variation" integer,
    "version" integer,
    "exam" integer
);

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

CREATE TABLE topics (
    "topic" SERIAL PRIMARY KEY,
    "course" integer REFERENCES courses("course") NOT NULL,
    "title" character varying(128) NOT NULL,
    "visibility" integer,
    "position" integer DEFAULT 1,
    "archived" boolean DEFAULT false
);

CREATE TABLE examqtemplates (
    "id" SERIAL NOT NULL,
    "exam" integer NOT NULL,
    "qtemplate" integer NOT NULL,
    "position" integer
);

CREATE TABLE examquestions (
    "id" SERIAL PRIMARY KEY,
    "exam" integer NOT NULL,
    "student" integer,
    "position" integer,
    "question" integer NOT NULL
);

CREATE TABLE exams (
    "exam" SERIAL PRIMARY KEY,
    "title" character varying(128) NOT NULL,
    "owner" integer,
    "type" integer,
    "start" timestamp without time zone,
    "end" timestamp without time zone,
    "description" text,
    "comments" text,
    "course" integer,
    "archived" integer DEFAULT 0,
    "duration" integer,
    "markstatus" integer DEFAULT 1,
    "code" character varying,
    "instant" integer
);

CREATE TABLE examtimers (
    "id" SERIAL PRIMARY KEY,
    "exam" integer NOT NULL,
    "userid" integer NOT NULL,
    "endtime" character varying(64)
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

CREATE TABLE marklog (
    "id" SERIAL PRIMARY KEY,
    "eventtime" timestamp without time zone,
    "exam" integer REFERENCES exams("exam"),
    "student" integer REFERENCES users("id"),
    "marker" integer,
    "operation" character varying(255),
    "value" character varying(64)
);

CREATE TABLE groupcourses (
    "id" SERIAL PRIMARY KEY,
    "groupid" integer REFERENCES ugroups("id") NOT NULL,
    "course" integer REFERENCES courses("course")NOT NULL
);

CREATE TABLE marks (
    "id" SERIAL PRIMARY KEY,
    "eventtime" timestamp,
    "marking" integer DEFAULT 0,
    "exam" integer REFERENCES exams("exam"),
    "student" integer REFERENCES users("id"),
    "position" integer,
    "qtemplate" integer REFERENCES qtemplates("qtemplate"),
    "question" integer REFERENCES questions("question"),
    "part" integer,
    "marker" integer,
    "manual" boolean,
    "official" boolean,
    "operation" character varying(255),
    "changed" boolean,
    "score" double precision
);

CREATE TABLE messages (
    "name" character varying(200) UNIQUE PRIMARY KEY,
    "object" integer DEFAULT 0,
    "type" integer DEFAULT 0,
    "updated" timestamp without time zone,
    "by" integer DEFAULT 0,
    "message" text
);

CREATE TABLE permissiondesc (
    "permission" SERIAL PRIMARY KEY,
    "name" character varying(80) NOT NULL,
    "description" character varying(255),
    "sharable" boolean DEFAULT true NOT NULL
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

CREATE TABLE permissions (
    "id" SERIAL PRIMARY KEY,
    "course" integer NOT NULL,
    "userid" integer references users("id"),
    "permission" integer REFERENCES permissiondesc("permission")
);

CREATE TABLE qattach (
    "qattach" SERIAL PRIMARY KEY,
    "qtemplate" integer REFERENCES qtemplates("qtemplate"),
    "variation" integer,
    "version" integer,
    "mimetype" character varying(250),
    "name" character varying(64),
    "data" bytea
);

CREATE TABLE qtattach (
    "qtattach" SERIAL PRIMARY KEY,
    "qtemplate" integer REFERENCES qtemplates("qtemplate"),
    "mimetype" character varying(250),
    "data" bytea,
    "version" integer,
    "name" character varying(64)
);

CREATE TABLE qtvariations (
    "id" SERIAL PRIMARY KEY,
    "qtemplate" integer NOT NULL,
    "variation" integer NOT NULL,
    "version" integer,
    "data" bytea
);

CREATE TABLE guesses (
    "id" SERIAL PRIMARY KEY,
    "question" integer REFERENCES questions("question"),
    "created" timestamp,
    "part" integer,
    "guess" text
);

CREATE TABLE questiontopics (
    "id" SERIAL PRIMARY KEY,
    "qtemplate" integer REFERENCES qtemplates("qtemplate") NOT NULL,
    "topic" integer REFERENCES topics("topic") NOT NULL,
    "position" integer
);

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

CREATE TABLE userexams (
    "id" SERIAL PRIMARY KEY,
    "exam" integer REFERENCES exams("exam") NOT NULL,
    "student" integer REFERENCES "users"("id"),
    "status" integer,
    "timeremain" integer,
    "submittime" timestamp,
    "score" real,
    "lastchange" timestamp
);

CREATE TABLE usergroups (
    "id" SERIAL PRIMARY KEY,
    "userid" integer REFERENCES users("id") NOT NULL,
    "groupid" integer REFERENCES ugroups("id") NOT NULL
);

CREATE TABLE config (
    "name" character varying(50) unique primary key,
    "value" text
);
INSERT INTO config ("name", "value") VALUES ('dbversion', '3.9.4');

CREATE SEQUENCE users_version_seq START WITH 1 INCREMENT BY 1 NO MINVALUE NO MAXVALUE CACHE 1;
CREATE SEQUENCE courses_version_seq START WITH 1 INCREMENT BY 1 NO MINVALUE NO MAXVALUE CACHE 1;

CREATE INDEX guesses_questioncreated ON guesses USING btree (question, created);
CREATE INDEX qattach_qtemplate_variation_version ON qattach USING btree (qtemplate, variation, version);
CREATE INDEX qtattach_qtemplate_version ON qtattach USING btree (qtemplate, version);
CREATE UNIQUE INDEX qtemplate_embed_idx ON qtemplates USING btree (embed_id);
CREATE INDEX qtvariations_qtemplate_variation ON qtvariations USING btree (qtemplate, variation);
CREATE INDEX qtvariations_qtemplate_version ON qtvariations USING btree (qtemplate, version);
CREATE INDEX question_qtemplate ON questions USING btree (qtemplate);
CREATE INDEX question_student ON questions USING btree (student);
CREATE INDEX stats_prac_q_course_qtemplate_idx ON stats_prac_q_course USING btree (qtemplate);
CREATE INDEX stats_prac_q_course_when_idx ON stats_prac_q_course USING btree ("when");
CREATE INDEX topics_course ON topics USING btree (course);
CREATE INDEX userexams_lastchange_idx ON userexams USING btree (lastchange);
CREATE INDEX usergroups_groupid ON usergroups USING btree (groupid);
CREATE INDEX usergroups_userid ON usergroups USING btree (userid);
CREATE INDEX users_uname_passwd ON users USING btree (uname, passwd);

