insert into constellation (fullname, shortname)
values ('GALILEO', 'GAL'),
       ('GLONASS', 'GLO'),
       ('GPS', 'GPS'),
       ('BEIDOU', 'BDS');

insert into observation_type (type)
values (null); -- absence d'observation dans la table `skyplot_used_band`
