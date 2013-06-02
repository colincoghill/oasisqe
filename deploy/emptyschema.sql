--
-- PostgreSQL database dump
--

SET statement_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SET check_function_bodies = false;
SET client_min_messages = warning;

CREATE EXTENSION IF NOT EXISTS plpgsql WITH SCHEMA pg_catalog;
COMMENT ON EXTENSION plpgsql IS 'PL/pgSQL procedural language';

SET search_path = public, pg_catalog;
SET default_tablespace = '';
SET default_with_oids = false;


CREATE SEQUENCE audit_id_seq START WITH 1 INCREMENT BY 1 NO MINVALUE NO MAXVALUE CACHE 1;
CREATE TABLE audit (
    "id" integer DEFAULT nextval('audit_id_seq'::regclass) NOT NULL,
    "time" timestamp without time zone,
    "class" integer DEFAULT 1,
    "instigator" integer DEFAULT 0,
    "object" integer DEFAULT 0,
    "module" character varying(200),
    "message" character varying(250),
    "longmesg" text
);

CREATE SEQUENCE courses_course_seq START WITH 1 INCREMENT BY 1 NO MINVALUE NO MAXVALUE CACHE 1;
CREATE TABLE courses (
    "course" integer DEFAULT nextval('courses_course_seq'::regclass) NOT NULL,
    "title" character varying(128) NOT NULL,
    "description" text,
    "owner" integer,
    "active" integer DEFAULT 1,
    "type" integer,
    "practice_visibility" character varying DEFAULT 'all'::character varying,
    "assess_visibility" character varying DEFAULT 'enrol'::character varying
);

CREATE SEQUENCE courses_version_seq START WITH 1 INCREMENT BY 1 NO MINVALUE NO MAXVALUE CACHE 1;

CREATE SEQUENCE examqtemplates_id_seq START WITH 1 INCREMENT BY 1 NO MINVALUE NO MAXVALUE CACHE 1;
CREATE TABLE examqtemplates (
    "id" integer DEFAULT nextval('examqtemplates_id_seq'::regclass) NOT NULL,
    "exam" integer NOT NULL,
    "qtemplate" integer NOT NULL,
    "position" integer
);

CREATE SEQUENCE examquestions_id_seq START WITH 1 INCREMENT BY 1 NO MINVALUE NO MAXVALUE CACHE 1;
CREATE TABLE examquestions (
    "id" integer DEFAULT nextval('examquestions_id_seq'::regclass) NOT NULL,
    "exam" integer NOT NULL,
    "student" integer,
    "position" integer,
    "question" integer NOT NULL
);

CREATE SEQUENCE exams_exam_seq START WITH 1 INCREMENT BY 1 NO MINVALUE NO MAXVALUE CACHE 1;
CREATE TABLE exams (
    "exam" integer DEFAULT nextval('exams_exam_seq'::regclass) NOT NULL,
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

CREATE SEQUENCE examtimers_id_seq START WITH 1 INCREMENT BY 1 NO MINVALUE NO MAXVALUE CACHE 1;
CREATE TABLE examtimers (
    "id" integer DEFAULT nextval('examtimers_id_seq'::regclass) NOT NULL,
    "exam" integer NOT NULL,
    "userid" integer NOT NULL,
    "endtime" character varying(64)
);

CREATE SEQUENCE groupcourses_id_seq START WITH 1 INCREMENT BY 1 NO MINVALUE NO MAXVALUE CACHE 1;
CREATE TABLE groupcourses (
    "id" integer DEFAULT nextval('groupcourses_id_seq'::regclass) NOT NULL,
    "group" integer REFERENCES ugroups("id") NOT NULL,
    "course" integer REFERENCES courses("course")NOT NULL
);

CREATE SEQUENCE periods_id_seq START WITH 1 INCREMENT BY 1 NO MINVALUE NO MAXVALUE CACHE 1;
CREATE TABLE periods (
    "id" integer DEFAULT nextval('periods_id_seq'::regclass) PRIMARY KEY,
    "name" character varying(50) UNIQUE NOT NULL,
    "title" character varying(250),
    "start" date,
    "finish" date,
    "code" character varying(50) unique
);

INSERT INTO periods ("name", "title", "start", "finish", "code") VALUES ('Indefinite', 'Indefinite', '2000-01-01', '9999-12-31','');
CREATE INDEX ON "periods" USING BTREE("name");
CREATE INDEX ON "periods" USING BTREE("code");

CREATE SEQUENCE feeds_id_seq START WITH 1 INCREMENT BY 1 NO MINVALUE NO MAXVALUE CACHE 1;
CREATE TABLE feeds (
    "id" integer DEFAULT nextval('feeds_id_seq'::regclass) PRIMARY KEY,
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

CREATE SEQUENCE ugroups_id_seq START WITH 1 INCREMENT BY 1 NO MINVALUE NO MAXVALUE CACHE 1;
CREATE TABLE ugroups (
    "id" integer DEFAULT nextval('ugroups_id_seq'::regclass) NOT NULL,
    "name" character varying UNIQUE,
    "title" character varying,
    "gtype" integer references grouptypes("type"),
    "source" character varying DEFAULT 'adhoc'::character varying,  -- "adhoc", "open", "feed"
    "feed" integer references feeds("id") NULL,
    "period" integer references periods("id"),
    "active" boolean default TRUE
);

CREATE SEQUENCE grouptypes_type_seq START WITH 1 INCREMENT BY 1 NO MINVALUE NO MAXVALUE CACHE 1;
CREATE TABLE grouptypes (
    "type" integer DEFAULT nextval('grouptypes_type_seq'::regclass) NOT NULL,
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

CREATE SEQUENCE guesses_id_seq START WITH 1 INCREMENT BY 1 NO MINVALUE NO MAXVALUE CACHE 1;
CREATE TABLE guesses (
    "id" integer DEFAULT nextval('guesses_id_seq'::regclass) NOT NULL,
    "question" integer REFERENCES questions("question"),
    "created" timestamp,
    "part" integer,
    "guess" text
);

CREATE SEQUENCE marklog_id_seq START WITH 1 INCREMENT BY 1 NO MINVALUE NO MAXVALUE CACHE 1;
CREATE TABLE marklog (
    "id" integer DEFAULT nextval('marklog_id_seq'::regclass) NOT NULL,
    "eventtime" timestamp without time zone,
    "exam" integer REFERENCES exams("exam"),
    "student" integer REFERENCES users("id"),
    "marker" integer,
    "operation" character varying(255),
    "value" character varying(64)
);

CREATE SEQUENCE marks_id_seq START WITH 1 INCREMENT BY 1 NO MINVALUE NO MAXVALUE CACHE 1;
CREATE TABLE marks (
    "id" integer DEFAULT nextval('marks_id_seq'::regclass) NOT NULL,
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
    "name" character varying(200),
    "object" integer DEFAULT 0,
    "type" integer DEFAULT 0,
    "updated" timestamp without time zone,
    "by" integer DEFAULT 0,
    "message" text
);

CREATE SEQUENCE permissiondesc_permission_seq START WITH 1 INCREMENT BY 1 NO MINVALUE NO MAXVALUE CACHE 1;
CREATE TABLE permissiondesc (
    "permission" integer DEFAULT nextval('permissiondesc_permission_seq'::regclass) NOT NULL,
    "name" character varying(80) NOT NULL,
    "description" character varying(255),
    "sharable" boolean DEFAULT true NOT NULL
);

CREATE SEQUENCE permissions_id_seq START WITH 1 INCREMENT BY 1 NO MINVALUE NO MAXVALUE CACHE 1;
CREATE TABLE permissions (
    "id" integer DEFAULT nextval('permissions_id_seq'::regclass) NOT NULL,
    "course" integer NOT NULL,
    "userid" integer references users("id"),
    "permission" integer REFERENCES permissiondesc("permission")
);

CREATE SEQUENCE qattach_qattach_seq START WITH 1 INCREMENT BY 1 NO MINVALUE NO MAXVALUE CACHE 1;
CREATE TABLE qattach (
    "qattach" integer DEFAULT nextval('qattach_qattach_seq'::regclass) NOT NULL,
    "qtemplate" integer REFERENCES qtemplates("qtemplate"),
    "variation" integer,
    "version" integer,
    "mimetype" character varying(250),
    "name" character varying(64),
    "data" bytea
);

CREATE SEQUENCE qtattach_qtattach_seq START WITH 1 INCREMENT BY 1 NO MINVALUE NO MAXVALUE CACHE 1;
CREATE TABLE qtattach (
    "qtattach" integer DEFAULT nextval('qtattach_qtattach_seq'::regclass) NOT NULL,
    "qtemplate" integer REFERENCES qtemplates("qtemplate"),
    "mimetype" character varying(250),
    "data" bytea,
    "version" integer,
    "name" character varying(64)
);

CREATE SEQUENCE qtemplates_qtemplate_seq START WITH 1 INCREMENT BY 1 NO MINVALUE NO MAXVALUE CACHE 1;
CREATE TABLE qtemplates (
    "qtemplate" integer DEFAULT nextval('qtemplates_qtemplate_seq'::regclass) NOT NULL,
    "owner" integer REFERENCES users("id") NOT NULL,
    "title" character varying(128) NOT NULL,
    "description" text,
    "marker" integer,
    "scoremax" real,
    "version" integer,
    "status" integer,
    "embed_id" character varying(16)
);

CREATE SEQUENCE qtvariations_id_seq START WITH 1 INCREMENT BY 1 NO MINVALUE NO MAXVALUE CACHE 1;
CREATE TABLE qtvariations (
    "id" integer DEFAULT nextval('qtvariations_id_seq'::regclass) NOT NULL,
    "qtemplate" integer NOT NULL,
    "variation" integer NOT NULL,
    "version" integer,
    "data" bytea
);

CREATE SEQUENCE questions_question_seq START WITH 1 INCREMENT BY 1 NO MINVALUE NO MAXVALUE CACHE 1;
CREATE TABLE questions (
    "question" integer DEFAULT nextval('questions_question_seq'::regclass) NOT NULL,
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

CREATE SEQUENCE questiontopics_id_seq START WITH 1 INCREMENT BY 1 NO MINVALUE NO MAXVALUE CACHE 1;
CREATE TABLE questiontopics (
    "id" integer DEFAULT nextval('questiontopics_id_seq'::regclass) NOT NULL,
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

CREATE SEQUENCE topics_topic_seq START WITH 1 INCREMENT BY 1 NO MINVALUE NO MAXVALUE CACHE 1;
CREATE TABLE topics (
    "topic" integer DEFAULT nextval('topics_topic_seq'::regclass) NOT NULL,
    "course" integer REFERENCES courses("course") NOT NULL,
    "title" character varying(128) NOT NULL,
    "visibility" integer,
    "position" integer DEFAULT 1,
    "archived" boolean DEFAULT false
);

CREATE SEQUENCE userexams_id_seq START WITH 1 INCREMENT BY 1 NO MINVALUE NO MAXVALUE CACHE 1;
CREATE TABLE userexams (
    "id" integer DEFAULT nextval('userexams_id_seq'::regclass) NOT NULL,
    "exam" integer REFERENCES exams("exam") NOT NULL,
    "student" integer REFERENCES "user"("id"),
    "status" integer,
    "timeremain" integer,
    "submittime" timestamp,
    "score" real,
    "lastchange" timestamp
);

CREATE SEQUENCE usergroups_id_seq START WITH 1 INCREMENT BY 1 NO MINVALUE NO MAXVALUE CACHE 1;
CREATE TABLE usergroups (
    "id" integer DEFAULT nextval('usergroups_id_seq'::regclass) NOT NULL,
    "userid" integer REFERENCES users("id") NOT NULL,
    "groupid" integer REFERENCES ugroups("id") NOT NULL
);

CREATE SEQUENCE users_id_seq START WITH 1 INCREMENT BY 1 NO MINVALUE NO MAXVALUE CACHE 1;
CREATE TABLE users (
    "id" integer DEFAULT nextval('users_id_seq'::regclass) NOT NULL,
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

CREATE TABLE config (
    "name" character varying(50) unique,
    "value" text
);
INSERT INTO config ("name", "value") VALUES ('dbversion', '3.9.2');


CREATE SEQUENCE users_version_seq START WITH 1 INCREMENT BY 1 NO MINVALUE NO MAXVALUE CACHE 1;

ALTER TABLE ONLY courses ADD CONSTRAINT courses_pkey PRIMARY KEY (course);
ALTER TABLE ONLY examqtemplates ADD CONSTRAINT examqtemplates_pkey PRIMARY KEY (id);
ALTER TABLE ONLY examquestions ADD CONSTRAINT examquestions_pkey PRIMARY KEY (id);
ALTER TABLE ONLY exams ADD CONSTRAINT exams_pkey PRIMARY KEY (exam);
ALTER TABLE ONLY examtimers ADD CONSTRAINT examtimers_pkey PRIMARY KEY (id);
ALTER TABLE ONLY groupcourses ADD CONSTRAINT groupcourses_pkey PRIMARY KEY (id);
ALTER TABLE ONLY ugroups ADD CONSTRAINT groups_pkey PRIMARY KEY (id);
ALTER TABLE ONLY grouptypes ADD CONSTRAINT grouptypes_pkey PRIMARY KEY ("type");
ALTER TABLE ONLY guesses ADD CONSTRAINT guesses_pkey PRIMARY KEY (id);
ALTER TABLE ONLY marklog ADD CONSTRAINT marklog_pkey PRIMARY KEY (id);
ALTER TABLE ONLY marks ADD CONSTRAINT marks_pkey PRIMARY KEY (id);
ALTER TABLE ONLY permissions ADD CONSTRAINT permissions_pkey PRIMARY KEY (id);
ALTER TABLE ONLY qattach ADD CONSTRAINT qattach_pkey PRIMARY KEY (qattach);
ALTER TABLE ONLY qtattach ADD CONSTRAINT qtattach_pkey PRIMARY KEY (qtattach);
ALTER TABLE ONLY qtemplates ADD CONSTRAINT qtemplates_embed_id_key UNIQUE (embed_id);
ALTER TABLE ONLY qtemplates ADD CONSTRAINT qtemplates_pkey PRIMARY KEY (qtemplate);
ALTER TABLE ONLY qtvariations ADD CONSTRAINT qtvariations_pkey PRIMARY KEY (id);
ALTER TABLE ONLY questions ADD CONSTRAINT questions_pkey PRIMARY KEY (question);
ALTER TABLE ONLY questiontopics ADD CONSTRAINT questiontopics_pkey PRIMARY KEY (id);
ALTER TABLE ONLY topics ADD CONSTRAINT topics_pkey PRIMARY KEY (topic);
ALTER TABLE ONLY userexams ADD CONSTRAINT userexams_pkey PRIMARY KEY (id);
ALTER TABLE ONLY usergroups ADD CONSTRAINT usergroups_pkey PRIMARY KEY (id);
ALTER TABLE ONLY users ADD CONSTRAINT users_pkey PRIMARY KEY (id);


CREATE INDEX guesses_questioncreated ON guesses USING btree (question, created);
CREATE INDEX qattach_qtemplate_variation_version ON qattach USING btree (qtemplate, variation, version);
CREATE INDEX qtattach_qtemplate_version ON qtattach USING btree (qtemplate, version);
CREATE UNIQUE INDEX qtemplate_embed_idx ON qtemplates USING btree (embed_id);
CREATE INDEX qtemplates_qtemplate ON qtemplates USING btree (qtemplate);
CREATE INDEX qtvariations_qtemplate_variation ON qtvariations USING btree (qtemplate, variation);
CREATE INDEX qtvariations_qtemplate_version ON qtvariations USING btree (qtemplate, version);
CREATE INDEX question_qtemplate ON questions USING btree (qtemplate);
CREATE INDEX question_student ON questions USING btree (student);
CREATE INDEX questions_question ON questions USING btree (question);
CREATE INDEX stats_prac_q_course_qtemplate_idx ON stats_prac_q_course USING btree (qtemplate);
CREATE INDEX stats_prac_q_course_when_idx ON stats_prac_q_course USING btree ("when");
CREATE INDEX topics_course ON topics USING btree (course);
CREATE INDEX userexams_lastchange_idx ON userexams USING btree (lastchange);
CREATE INDEX usergroups_groupid ON usergroups USING btree (groupid);
CREATE INDEX usergroups_userid ON usergroups USING btree (userid);
CREATE INDEX users_uname_passwd ON users USING btree (uname, passwd);

