------------------------------------------------------------------------------------------------------------------------
-- Tables de bases

create table constellation (
    id smallserial constraint satellite_system_pk primary key,
    fullname varchar(10) not null,
    shortname varchar(4) not null
);

create table network (
    id smallserial constraint network_pk primary key,
    name varchar(20) not null
);

create table observation_type (
    id smallserial constraint observation_type_pk primary key,
    type varchar(3) not null
);

create table station (
    id smallserial constraint station_pk primary key,
    shortname varchar(4) not null,
    fullname varchar(9) not null
);

create table station_network (
    station_id smallserial
        constraint station_network_station_id_fk references station
        on delete cascade,
    network_id smallserial
        constraint station_network_network_id_fk references network
        on delete cascade,
    constraint station_network_pk primary key (station_id, network_id)
);

------------------------------------------------------------------------------------------------------------------------
-- Tables de séries temporelles

create table sig2noise (
    id bigserial constraint snr_pk primary key,
    date date not null,
    station_id smallserial
        constraint snr_station_id_fk references station
        on delete cascade,
    constellation_id smallserial
        constraint snr_constellation_id_fk references constellation
        on delete cascade,
    observation_type_id smallserial
        constraint snr_observation_type_id_fk references observation_type
        on delete cascade,
    value real not null
);

create table multipath (
    id bigserial constraint multipath_pk primary key,
    date date not null,
    station_id smallserial
        constraint multipath_station_id_fk references station
        on delete cascade,
    constellation_id smallserial
        constraint multipath_constellation_id_fk references constellation
        on delete cascade,
    observation_type_id smallserial
        constraint multipath_observation_type_id_fk references observation_type
        on delete cascade,
    value real not null
);

create table observation_cs (
    id bigserial constraint observation_cs_pk primary key,
    date date not null,
    station_id smallserial
        constraint observation_cs_station_id_fk references station
        on delete cascade,
    constellation_id smallserial
        constraint observation_cs_constellation_id_fk references constellation
        on delete cascade,
    value real not null
);

create table satellite_cs (
    id bigserial constraint satellite_cs_pk primary key,
    date date not null,
    station_id smallserial
        constraint satellite_cs_station_id_fk references station
        on delete cascade,
    constellation_id smallserial
        constraint satellite_cs_constellation_id_fk references constellation
        on delete cascade,
    value real not null
);

create table skyplot (
    id bigserial constraint skyplot_pk primary key,
    datetime timestamp not null,
    station_id smallserial
        constraint skyplot_station_id_fk references station
        on delete cascade,
    constellation_id smallserial
        constraint skyplot_constellation_id_fk references constellation
        on delete cascade,
    satellite smallint not null,
    elevation smallint not null,
    azimut smallint not null,
    mp1 smallint not null,
    mp2 smallint not null,
    mp5 smallint not null,
    snr1 smallint not null,
    snr2 smallint not null,
    snr5 smallint not null,
    unique (datetime, station_id, constellation_id, satellite)
);
