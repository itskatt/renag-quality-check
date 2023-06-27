------------------------------------------------------------------------------------------------------------------------
-- Tables des réseaux et stations

create table network (
    id smallserial constraint network_pk primary key,
    name varchar(20) unique not null
);

create table station (
    id smallserial constraint station_pk primary key,
    network_id smallint
        constraint station_network_id_fk references network
        on delete cascade,
    shortname varchar(4) not null,
    fullname varchar(9) not null,
    lat double precision,
    long double precision,
    unique (fullname, network_id)
);

------------------------------------------------------------------------------------------------------------------------
-- Tables de données de bases partagées entre les tables de données de graphes

create table constellation (
    id smallserial constraint satellite_system_pk primary key,
    fullname varchar(10) unique not null,
    shortname varchar(4) unique not null
);

create table observation_type (
    id smallserial constraint observation_type_pk primary key,
    type varchar(3) unique
);

------------------------------------------------------------------------------------------------------------------------
-- Table pour accélérer la découverte des fichiers déjà insérés

create table inserted_file (
    id serial constraint inserted_file_pk primary key,
    name varchar(20) not null,
    station_id smallint
        constraint inserted_file_station_id_fk references station
        on delete cascade,
    unique (name, station_id)
);

------------------------------------------------------------------------------------------------------------------------
-- Tables de séries temporelles

create table sig2noise (
    id bigserial constraint snr_pk primary key,
    date date not null,
    station_id smallint
        constraint snr_station_id_fk references station
        on delete cascade,
    constellation_id smallint
        constraint snr_constellation_id_fk references constellation
        on delete cascade,
    observation_type_id smallint
        constraint snr_observation_type_id_fk references observation_type
        on delete cascade,
    value real not null
);

create table multipath (
    id bigserial constraint multipath_pk primary key,
    date date not null,
    station_id smallint
        constraint multipath_station_id_fk references station
        on delete cascade,
    constellation_id smallint
        constraint multipath_constellation_id_fk references constellation
        on delete cascade,
    observation_type_id smallint
        constraint multipath_observation_type_id_fk references observation_type
        on delete cascade,
    value real not null
);

create table observation_cs (
    id bigserial constraint observation_cs_pk primary key,
    date date not null,
    station_id smallint
        constraint observation_cs_station_id_fk references station
        on delete cascade,
    constellation_id smallint
        constraint observation_cs_constellation_id_fk references constellation
        on delete cascade,
    value real not null
);

create table satellite_cs (
    id bigserial constraint satellite_cs_pk primary key,
    date date not null,
    station_id smallint
        constraint satellite_cs_station_id_fk references station
        on delete cascade,
    constellation_id smallint
        constraint satellite_cs_constellation_id_fk references constellation
        on delete cascade,
    value real not null
);

------------------------------------------------------------------------------------------------------------------------
-- Table de skyplot

create table skyplot_date (
    id serial constraint skyplot_date_pk primary key,
    date date not null,
    unique (date)
);

create table skyplot_used_band (
    id serial constraint skyplot_used_band_pk primary key,
    date_id integer
        constraint skyplot_date_id_fk references skyplot_date,
    station_id smallint
        constraint satellite_cs_station_id_fk references station
        on delete cascade,
    constellation_id smallint
        constraint skyplot_constellation_id_fk references constellation
        on delete cascade,
    mp1_observation_type_id smallint
        constraint mp1_skyplot_used_band_observation_type_id_fk references observation_type
        on delete cascade,
    mp2_observation_type_id smallint
        constraint mp2_skyplot_used_band_observation_type_id_fk references observation_type
        on delete cascade,
    mp5_observation_type_id smallint
        constraint mp5_skyplot_used_band_observation_type_id_fk references observation_type
        on delete cascade,
    sig2noise1_observation_type_id smallint
        constraint sig2noise1_skyplot_used_band_observation_type_id_fk references observation_type
        on delete cascade,
    sig2noise2_observation_type_id smallint
        constraint sig2noise2_skyplot_used_band_observation_type_id_fk references observation_type
        on delete cascade,
    sig2noise5_observation_type_id smallint
        constraint sig2noise5_skyplot_used_band_observation_type_id_fk references observation_type
        on delete cascade,
    unique (date_id, station_id, constellation_id)
);

create table skyplot (
    id bigserial constraint skyplot_pk primary key,
    datetime timestamp not null,
    date_id integer
        constraint skyplot_date_id_fk references skyplot_date,
    station_id smallint
        constraint skyplot_station_id_fk references station
        on delete cascade,
    constellation_id smallint
        constraint skyplot_constellation_id_fk references constellation
        on delete cascade,
    satellite smallint not null,
    elevation smallint not null,
    azimut smallint not null,
    mp1 smallint,
    mp2 smallint,
    mp5 smallint,
    sig2noise1 smallint,
    sig2noise2 smallint,
    sig2noise5 smallint,
    cs1 boolean not null default false,
    cs2 boolean not null default false,
    cs5 boolean not null default false,
    unique (datetime, station_id, constellation_id, satellite)
);
