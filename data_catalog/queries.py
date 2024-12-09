schema_catalog = """
select 
    n.nspname as schema_name,
    r.rolname as owner,
    count(distinct t.tablename) as table_count,
    count(distinct v.viewname) as view_count,
    count(distinct p.proname) as function_count
from pg_catalog.pg_namespace n
left join pg_catalog.pg_roles r 
    on n.nspowner = r.oid
left join pg_catalog.pg_tables t 
    on t.schemaname = n.nspname
left join pg_catalog.pg_views v 
    on v.schemaname = n.nspname
left join pg_catalog.pg_proc p 
    on p.pronamespace = n.oid
where
    n.nspname not in ('pg_catalog', 'information_schema')
    and n.nspname !~ '^pg_temp'
    and n.nspname !~ '^pg_toast'
    and n.nspname !~ '^pg_toast_temp'
group by n.nspname, r.rolname
order by n.nspname;
"""

table_catalog = """
select 
    schemaname as schema,
    tablename as table_name,
    tableowner as owner,
    hasindexes as has_indexes,
    hasrules as has_rules,
    hastriggers as has_triggers
from pg_catalog.pg_tables
where schemaname not in ('pg_catalog', 'information_schema')
order by schemaname, tablename;
"""

view_catalog = """
select
    v.schemaname as schema,
    v.viewname as view_name,
    v.viewowner as owner,
    case 
        when m.matviewname is not null then 'Materialized View'
        else 'View'
    end as view_type,
    v.definition
from pg_catalog.pg_views as v
left join pg_catalog.pg_matviews as m
    on
        v.schemaname = m.schemaname
        and v.viewname = m.matviewname
where v.schemaname not in ('pg_catalog', 'information_schema')
order by v.schemaname, v.viewname;
"""

function_catalog = """
select 
    n.nspname as schema,
    p.proname as function_name,
    r.rolname as owner,
    case p.prokind 
        when 'f' then 'function'
        when 'p' then 'procedure' 
        when 'a' then 'aggregate'
        when 'w' then 'window'
    end as function_type,
    pg_get_function_arguments(p.oid) as arguments,
    pg_get_function_result(p.oid) as return_type,
    case 
        when p.prokind = 'a' then null  
        else pg_get_functiondef(p.oid) 
    end as definition
from pg_catalog.pg_proc p
join pg_catalog.pg_namespace n 
    on p.pronamespace = n.oid
join pg_catalog.pg_roles r 
    on p.proowner = r.oid
where 
    n.nspname not in ('pg_catalog', 'information_schema')
    and r.rolname != 'postgres'
order by n.nspname, p.proname;
"""

query_dict = {

    "schema_catalog" : schema_catalog,
    "table_catalog" : table_catalog,
    "view_catalog" : view_catalog,
    "function_catalog" : function_catalog,

}