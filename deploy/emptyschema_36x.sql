
SET statement_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;

BEGIN;

CREATE SEQUENCE audit_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

CREATE TABLE audit (
    id integer DEFAULT nextval('audit_id_seq'::regclass) NOT NULL,
    "time" timestamp without time zone,
    class integer DEFAULT 1,
    instigator integer DEFAULT 0,
    object integer DEFAULT 0,
    module character varying(200),
    message character varying(250),
    longmesg text
);

CREATE SEQUENCE courses_course_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

CREATE TABLE courses (
    course integer DEFAULT nextval('courses_course_seq'::regclass) NOT NULL,
    title character varying(128) NOT NULL,
    description text,
    owner integer,
    active integer DEFAULT 1,
    type integer,
    enrol_type character varying DEFAULT 'manual'::character varying,
    enrol_location character varying,
    enrol_freq integer DEFAULT 120,
    registration character varying DEFAULT 'controlled'::character varying
);

CREATE SEQUENCE courses_version_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

CREATE SEQUENCE examqtemplates_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

CREATE TABLE examqtemplates (
    id integer DEFAULT nextval('examqtemplates_id_seq'::regclass) NOT NULL,
    exam integer NOT NULL,
    qtemplate integer NOT NULL,
    "position" integer
);

CREATE SEQUENCE examquestions_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

CREATE TABLE examquestions (
    id integer DEFAULT nextval('examquestions_id_seq'::regclass) NOT NULL,
    exam integer NOT NULL,
    student integer,
    "position" integer,
    question integer NOT NULL
);

CREATE SEQUENCE exams_exam_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

CREATE TABLE exams (
    exam integer DEFAULT nextval('exams_exam_seq'::regclass) NOT NULL,
    title character varying(128) NOT NULL,
    owner integer,
    type integer,
    start timestamp without time zone,
    "end" timestamp without time zone,
    description text,
    comments text,
    course integer,
    archived integer DEFAULT 0,
    duration integer,
    markstatus integer DEFAULT 1,
    code character varying,
    instant integer
);

CREATE SEQUENCE examtimers_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

CREATE TABLE examtimers (
    id integer DEFAULT nextval('examtimers_id_seq'::regclass) NOT NULL,
    exam integer NOT NULL,
    userid integer NOT NULL,
    endtime character varying(64)
);

CREATE SEQUENCE groupcourses_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

CREATE TABLE groupcourses (
    id integer DEFAULT nextval('groupcourses_id_seq'::regclass) NOT NULL,
    groupid integer NOT NULL,
    active integer DEFAULT 0,
    course integer NOT NULL
);

CREATE SEQUENCE groups_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

CREATE TABLE groups (
    id integer DEFAULT nextval('groups_id_seq'::regclass) NOT NULL,
    title character varying(128) NOT NULL,
    description text,
    owner integer,
    semester character varying(30),
    type integer
);

CREATE SEQUENCE grouptypes_type_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

CREATE TABLE grouptypes (
    type integer DEFAULT nextval('grouptypes_type_seq'::regclass) NOT NULL,
    title character varying(128) NOT NULL,
    description text
);

CREATE SEQUENCE guesses_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

CREATE TABLE guesses (
    id integer DEFAULT nextval('guesses_id_seq'::regclass) NOT NULL,
    question integer,
    created timestamp without time zone,
    part integer,
    guess text
);

CREATE SEQUENCE marklog_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

CREATE TABLE marklog (
    id integer DEFAULT nextval('marklog_id_seq'::regclass) NOT NULL,
    eventtime timestamp without time zone,
    exam integer,
    student integer,
    marker integer,
    operation character varying(255),
    value character varying(64)
);

CREATE SEQUENCE marks_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

CREATE TABLE marks (
    id integer DEFAULT nextval('marks_id_seq'::regclass) NOT NULL,
    eventtime timestamp without time zone,
    marking integer DEFAULT 0,
    exam integer,
    student integer,
    "position" integer,
    qtemplate integer,
    question integer,
    part integer,
    marker integer,
    manual boolean,
    official boolean,
    operation character varying(255),
    changed boolean,
    score double precision
);

CREATE TABLE messages (
    name character varying(200),
    object integer DEFAULT 0,
    type integer DEFAULT 0,
    updated timestamp without time zone,
    by integer DEFAULT 0,
    message text
);

CREATE SEQUENCE permissiondesc_permission_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

CREATE TABLE permissiondesc (
    permission integer DEFAULT nextval('permissiondesc_permission_seq'::regclass) NOT NULL,
    name character varying(80) NOT NULL,
    description character varying(255),
    sharable boolean DEFAULT true NOT NULL
);

CREATE SEQUENCE permissions_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

CREATE TABLE permissions (
    id integer DEFAULT nextval('permissions_id_seq'::regclass) NOT NULL,
    course integer NOT NULL,
    userid integer NOT NULL,
    permission integer
);

CREATE SEQUENCE qattach_qattach_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

CREATE TABLE qattach (
    qattach integer DEFAULT nextval('qattach_qattach_seq'::regclass) NOT NULL,
    qtemplate integer,
    variation integer,
    version integer,
    mimetype character varying(250),
    name character varying(64),
    data bytea
);

CREATE SEQUENCE qtattach_qtattach_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

CREATE TABLE qtattach (
    qtattach integer DEFAULT nextval('qtattach_qtattach_seq'::regclass) NOT NULL,
    qtemplate integer,
    mimetype character varying(250),
    data bytea,
    version integer,
    name character varying(64)
);

CREATE SEQUENCE qtemplates_qtemplate_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

CREATE TABLE qtemplates (
    qtemplate integer DEFAULT nextval('qtemplates_qtemplate_seq'::regclass) NOT NULL,
    owner integer NOT NULL,
    title character varying(128) NOT NULL,
    description text,
    marker integer,
    scoremax real,
    version integer,
    status integer,
    embed_id character varying(16)
);

CREATE SEQUENCE qtvariations_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

CREATE TABLE qtvariations (
    id integer DEFAULT nextval('qtvariations_id_seq'::regclass) NOT NULL,
    qtemplate integer NOT NULL,
    variation integer NOT NULL,
    version integer,
    data bytea
);

CREATE SEQUENCE questionflags_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

CREATE TABLE questionflags (
    id integer DEFAULT nextval('questionflags_id_seq'::regclass) NOT NULL,
    question integer DEFAULT 0,
    tag character varying(50),
    data character varying(200),
    "when" timestamp without time zone,
    by integer DEFAULT 0,
    active boolean DEFAULT true
);

CREATE SEQUENCE questions_question_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

CREATE TABLE questions (
    question integer DEFAULT nextval('questions_question_seq'::regclass) NOT NULL,
    qtemplate integer,
    status integer,
    name character varying(200),
    student integer,
    score real DEFAULT 0,
    firstview timestamp without time zone,
    marktime timestamp without time zone,
    variation integer,
    version integer,
    exam integer
);

CREATE SEQUENCE questiontopics_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

CREATE TABLE questiontopics (
    id integer DEFAULT nextval('questiontopics_id_seq'::regclass) NOT NULL,
    qtemplate integer NOT NULL,
    topic integer NOT NULL,
    "position" integer
);

CREATE TABLE stats_prac_q_course (
    qtemplate integer NOT NULL,
    "when" timestamp with time zone,
    hour integer NOT NULL,
    day integer NOT NULL,
    month integer NOT NULL,
    year integer NOT NULL,
    number integer NOT NULL,
    avgscore double precision
);

CREATE TABLE statsqtassesshourly (
    assesses bigint,
    starttime timestamp without time zone,
    qtemplate_id integer
);

CREATE TABLE statsqtpracticehourly (
    practices bigint,
    starttime timestamp without time zone,
    qtemplate_id integer
);

CREATE TABLE tips (
    id integer NOT NULL,
    title character varying(50),
    message text,
    owner integer DEFAULT 0,
    for_teachers boolean DEFAULT true,
    for_loginpage boolean DEFAULT true,
    for_students boolean DEFAULT true
);

CREATE SEQUENCE tips_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

ALTER SEQUENCE tips_id_seq OWNED BY tips.id;

CREATE SEQUENCE topics_topic_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

CREATE TABLE topics (
    topic integer DEFAULT nextval('topics_topic_seq'::regclass) NOT NULL,
    course integer NOT NULL,
    title character varying(128) NOT NULL,
    visibility integer,
    "position" integer DEFAULT 1,
    archived boolean DEFAULT false
);

CREATE SEQUENCE userexams_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

CREATE TABLE userexams (
    id integer DEFAULT nextval('userexams_id_seq'::regclass) NOT NULL,
    exam integer NOT NULL,
    student integer,
    status integer,
    timeremain integer,
    submittime timestamp without time zone,
    score integer,
    lastchange timestamp without time zone
);

CREATE SEQUENCE usergroups_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

CREATE TABLE usergroups (
    id integer DEFAULT nextval('usergroups_id_seq'::regclass) NOT NULL,
    userid integer NOT NULL,
    groupid integer NOT NULL,
    type integer,
    semester character varying
);

CREATE SEQUENCE users_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

CREATE TABLE users (
    id integer DEFAULT nextval('users_id_seq'::regclass) NOT NULL,
    uname character varying(12),
    passwd character varying(250),
    givenname character varying(80),
    familyname character varying(80),
    student_id character varying(20),
    acctstatus integer,
    email character varying,
    source character varying,
    expiry timestamp with time zone
);

CREATE SEQUENCE users_version_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

ALTER TABLE ONLY tips
    ALTER COLUMN id SET DEFAULT nextval('tips_id_seq'::regclass);

ALTER TABLE ONLY courses
    ADD CONSTRAINT courses_pkey PRIMARY KEY (course);

ALTER TABLE ONLY examqtemplates
    ADD CONSTRAINT examqtemplates_pkey PRIMARY KEY (id);

ALTER TABLE ONLY examquestions
    ADD CONSTRAINT examquestions_pkey PRIMARY KEY (id);

ALTER TABLE ONLY exams
    ADD CONSTRAINT exams_pkey PRIMARY KEY (exam);

ALTER TABLE ONLY examtimers
    ADD CONSTRAINT examtimers_pkey PRIMARY KEY (id);

ALTER TABLE ONLY groupcourses
    ADD CONSTRAINT groupcourses_pkey PRIMARY KEY (id);

ALTER TABLE ONLY groups
    ADD CONSTRAINT groups_pkey PRIMARY KEY (id);

ALTER TABLE ONLY grouptypes
    ADD CONSTRAINT grouptypes_pkey PRIMARY KEY (type);

ALTER TABLE ONLY guesses
    ADD CONSTRAINT guesses_pkey PRIMARY KEY (id);

ALTER TABLE ONLY marklog
    ADD CONSTRAINT marklog_pkey PRIMARY KEY (id);

ALTER TABLE ONLY marks
    ADD CONSTRAINT marks_pkey PRIMARY KEY (id);

ALTER TABLE ONLY permissiondesc
    ADD CONSTRAINT permissiondesc_pkey PRIMARY KEY (permission);

ALTER TABLE ONLY permissions
    ADD CONSTRAINT permissions_pkey PRIMARY KEY (id);

ALTER TABLE ONLY qattach
    ADD CONSTRAINT qattach_pkey PRIMARY KEY (qattach);

ALTER TABLE ONLY qtattach
    ADD CONSTRAINT qtattach_pkey PRIMARY KEY (qtattach);

ALTER TABLE ONLY qtemplates
    ADD CONSTRAINT qtemplates_embed_id_key UNIQUE (embed_id);

ALTER TABLE ONLY qtemplates
    ADD CONSTRAINT qtemplates_pkey PRIMARY KEY (qtemplate);

ALTER TABLE ONLY qtvariations
    ADD CONSTRAINT qtvariations_pkey PRIMARY KEY (id);

ALTER TABLE ONLY questions
    ADD CONSTRAINT questions_pkey PRIMARY KEY (question);

ALTER TABLE ONLY questiontopics
    ADD CONSTRAINT questiontopics_pkey PRIMARY KEY (id);

ALTER TABLE ONLY topics
    ADD CONSTRAINT topics_pkey PRIMARY KEY (topic);

ALTER TABLE ONLY userexams
    ADD CONSTRAINT userexams_pkey PRIMARY KEY (id);

ALTER TABLE ONLY usergroups
    ADD CONSTRAINT usergroups_pkey PRIMARY KEY (id);

ALTER TABLE ONLY users
    ADD CONSTRAINT users_pkey PRIMARY KEY (id);

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


commit;