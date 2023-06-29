-- Initialises the postgres database for the quality check data on docker container creation

-- create the database
create database quality_check_data;

-- connect to the database
\c quality_check_data

-- create the user for grafana
revoke all on schema public from public;

-- create the user for grafana
create user grafana_reader with password 'grafana';

-- grant the user access to the database and restrict access to select only
grant connect on database quality_check_data to grafana_reader;
grant usage on schema public to grafana_reader;
grant select on all tables in schema public to grafana_reader;

-- import the schema
\i /docker-entrypoint-initdb.d/schema.sql0

-- import initial data
\i /docker-entrypoint-initdb.d/inserts.sql0

-- create the indexes
\i /docker-entrypoint-initdb.d/create_indexes.sql0
