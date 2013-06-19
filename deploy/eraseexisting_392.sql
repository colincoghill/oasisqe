
SET statement_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;

BEGIN;
DROP TABLE IF EXISTS audit;
DROP TABLE IF EXISTS examqtemplates;
DROP TABLE IF EXISTS examquestions;

DROP TABLE IF EXISTS examtimers;
DROP TABLE IF EXISTS groupcourses;
DROP TABLE IF EXISTS usergroups;
DROP TABLE IF EXISTS ugroups;
DROP TABLE IF EXISTS periods;
DROP TABLE IF EXISTS feeds;
DROP TABLE IF EXISTS grouptypes;

DROP TABLE IF EXISTS marklog;

DROP TABLE IF EXISTS marks;
DROP TABLE IF EXISTS guesses;

DROP TABLE IF EXISTS messages;
DROP TABLE IF EXISTS permissions;
DROP TABLE IF EXISTS permissiondesc;

DROP TABLE IF EXISTS questions;
DROP TABLE IF EXISTS qattach;
DROP TABLE IF EXISTS qtattach;
DROP TABLE IF EXISTS qtvariations;

DROP TABLE IF EXISTS questiontopics;
DROP TABLE IF EXISTS topics;
DROP TABLE IF EXISTS userexams;
DROP TABLE IF EXISTS exams;
DROP TABLE IF EXISTS courses;
DROP TABLE IF EXISTS stats_prac_q_course;


DROP TABLE IF EXISTS qtemplates;
DROP TABLE IF EXISTS users;
DROP TABLE IF EXISTS config;

DROP SEQUENCE IF EXISTS users_version_seq;
DROP SEQUENCE IF EXISTS courses_version_seq;
COMMIT;