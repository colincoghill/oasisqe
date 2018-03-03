
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
DROP TABLE IF EXISTS groups;
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
DROP TABLE IF EXISTS questionflags;
DROP TABLE IF EXISTS questiontopics;
DROP TABLE IF EXISTS topics;
DROP TABLE IF EXISTS userexams;
DROP TABLE IF EXISTS exams;
DROP TABLE IF EXISTS courses;
DROP TABLE IF EXISTS stats_prac_q_course;

DROP TABLE IF EXISTS statsqtassesshourly;
DROP TABLE IF EXISTS statsqtpracticehourly;
DROP TABLE IF EXISTS tips;

DROP TABLE IF EXISTS qtemplates;
DROP TABLE IF EXISTS users;
DROP TABLE IF EXISTS userfeeds;
DROP TABLE IF EXISTS config;

DROP SEQUENCE IF EXISTS users_version_seq;
DROP SEQUENCE IF EXISTS courses_version_seq;
DROP SEQUENCE IF EXISTS audit_id_seq;
DROP SEQUENCE IF EXISTS audit_id_seq;
DROP SEQUENCE IF EXISTS courses_course_seq;
DROP SEQUENCE IF EXISTS examqtemplates_id_seq;
DROP SEQUENCE IF EXISTS examquestions_id_seq;
DROP SEQUENCE IF EXISTS exams_exam_seq;
DROP SEQUENCE IF EXISTS examtimers_id_seq;
DROP SEQUENCE IF EXISTS groupcourses_id_seq;
DROP SEQUENCE IF EXISTS grouptypes_type_seq;
DROP SEQUENCE IF EXISTS groups_id_seq;
DROP SEQUENCE IF EXISTS guesses_id_seq;
DROP SEQUENCE IF EXISTS marklog_id_seq;
DROP SEQUENCE IF EXISTS marks_id_seq;
DROP SEQUENCE IF EXISTS permissiondesc_permission_seq;
DROP SEQUENCE IF EXISTS permissions_id_seq;
DROP SEQUENCE IF EXISTS qattach_qattach_seq;
DROP SEQUENCE IF EXISTS qtattach_qtattach_seq;
DROP SEQUENCE IF EXISTS qtemplates_qtemplate_seq;
DROP SEQUENCE IF EXISTS qtvariations_id_seq;
DROP SEQUENCE IF EXISTS questions_question_seq;
DROP SEQUENCE IF EXISTS questiontopics_id_seq;
DROP SEQUENCE IF EXISTS questionflags_id_seq;
DROP SEQUENCE IF EXISTS topics_topic_seq;
DROP SEQUENCE IF EXISTS userexams_id_seq;
DROP SEQUENCE IF EXISTS usergroups_id_seq;
DROP SEQUENCE IF EXISTS users_id_seq;
DROP SEQUENCE IF EXISTS userfeeds_id_seq;
COMMIT;