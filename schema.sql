CREATE TABLE IF NOT EXISTS infractions 
(
"id" SERIAL,
"guild" BIGINT,
"moderator" BIGINT,
"target" BIGINT,
"type" VARCHAR,
"reason" VARCHAR,
"real_id" BIGINT,
"time_punished" TIMESTAMP,
"action_id" BIGINT
);

CREATE TABLE IF NOT EXISTS guild
(
"guild" BIGINT,
"prefix" VARCHAR,
"roles_to_watch" BIGINT,
"case_to_start" BIGINT,
"default_reason" VARCHAR,
"ping_user" BOOLEAN,
"logs_hugh" BOOLEAN,
"log_channel" BIGINT
);