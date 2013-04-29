
--  Run against a 3.6.x OASIS database, will make the changes needed for 3.8 to run.
--  Shouldn't break 3.6.x software, so you can go back, but there are some extra fields 3.8 needs


ALTER TABLE "public"."users" ALTER COLUMN "passwd" TYPE character varying(250);

ALTER TABLE "public"."users" ADD COLUMN "email" CHARACTER VARYING NULL;

ALTER TABLE "public"."users" ADD COLUMN "confirmation_code" CHARACTER VARYING NULL;
ALTER TABLE "public"."users" ADD COLUMN "confirmed" CHARACTER VARYING;

ALTER TABLE "public"."users" ADD COLUMN "source" CHARACTER VARYING NULL;   -- account is 'local' or 'netaccount'
ALTER TABLE "public"."users" ADD COLUMN "expiry" timestamptz NULL;
ALTER TABLE "public"."usergroups" ADD COLUMN "semester" CHARACTER VARYING NULL;   -- semester/time period code

ALTER TABLE "public"."exams" ADD COLUMN "code" CHARACTER VARYING NULL;   -- assessment password
ALTER TABLE "public"."exams" ADD COLUMN "instant" INTEGER NULL;

ALTER TABLE "public"."qtattach" ALTER COLUMN "mimetype" TYPE character varying(250);
ALTER TABLE "public"."qattach" ALTER COLUMN "mimetype" TYPE character varying(250);

ALTER TABLE "public"."courses" ADD COLUMN "enrol_type" CHARACTER VARYING DEFAULT 'manual';  --   manual, file, url, ldap
ALTER TABLE "public"."courses" ADD COLUMN "registration" CHARACTER VARYING DEFAULT 'controlled';
ALTER TABLE "public"."courses" ADD COLUMN "enrol_location" CHARACTER VARYING NULL;  -- if enrol type is URL or FILE, it's details
                                                                           -- if it's LDAP, the LDAP group name
ALTER TABLE "public"."courses" ADD COLUMN "enrol_freq" INTEGER DEFAULT '120';  -- How often (minutes) to refresh enrolment info
ALTER TABLE "public"."courses" ADD COLUMN "practice_visibility" CHARACTER VARYING DEFAULT 'all';
ALTER TABLE "public"."courses" ADD COLUMN "assess_visibility" CHARACTER VARYING DEFAULT 'enrol';


-- startdate and enddate allow enrolment in a group to come and go.
ALTER TABLE "public"."groups" ADD COLUMN "startdate" TIMESTAMP NULL; -- When the group takes effect
ALTER TABLE "public"."groups" ADD COLUMN "enddate" TIMESTAMP NULL; -- When the group ceases to take effect
ALTER TABLE "public"."groups" ADD COLUMN "enrol_type" CHARACTER VARYING DEFAULT 'manual';
ALTER TABLE "public"."groups" ADD COLUMN "registration" CHARACTER VARYING DEFAULT 'controlled';



CREATE TABLE stats_prac_q_course (
    "qtemplate"  INTEGER NOT NULL,
    "when" TIMESTAMPTZ,
    "hour"  INTEGER NOT NULL,
    "day"   INTEGER NOT NULL,
    "month"  INTEGER NOT NULL,
    "year"   INTEGER NOT NULL,
    "number"  INTEGER NOT NULL,
    "avgscore" FLOAT NULL
);
CREATE INDEX stats_prac_q_course_when_idx ON stats_prac_q_course USING btree ("when");
CREATE INDEX stats_prac_q_course_qtemplate_idx ON stats_prac_q_course USING btree ("qtemplate");
