do $$
    declare
        name text;
    begin
        for name in (
            select indexname
            from pg_indexes
            where tablename = 'skyplot' and
                  starts_with(indexname, 'speed-')
        ) loop
            execute 'drop index ' || quote_ident(name) || ';';
        end loop;
    end;
$$;
