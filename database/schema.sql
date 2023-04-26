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
    station_id smallserial constraint station_network_station_id_fk references station,
    network_id smallserial constraint station_network_network_id_fk references network,
    constraint station_network_pk primary key (station_id, network_id)
);

create table sig2noise (
    id bigserial constraint snr_pk primary key,
    date date not null,
    station_id smallserial constraint snr_station_id_fk references station,
    constellation_id smallserial constraint snr_constellation_id_fk references constellation,
    observation_type_id smallserial constraint snr_observation_type_id_fk references observation_type,
    value real
);