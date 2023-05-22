------------------------------------------------------------------------------------------------------------------------
-- Indexes pour les skyplot de cs

create index concurrently "speed-skyplot-cs1"
on skyplot(station_id)
where cs1;

create index concurrently "speed-skyplot-cs2"
on skyplot(station_id)
where cs2;

create index concurrently "speed-skyplot-cs5"
on skyplot(station_id)
where cs5;

------------------------------------------------------------------------------------------------------------------------
-- Indexes pour les autres skyplots

create index concurrently "speed-skyplot-station-date"
on skyplot(station_id, date_id);
