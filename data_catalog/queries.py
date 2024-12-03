# High level queries show overview of database objects
HIGH_LEVEL_QUERIES = {

    # Excludes postgres internal / system schemas
    # Excludes temporary schemas createdduring the session
    # Excludes TOAST schemas
    "schema": """
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
    """,

    # Excludes system schemas
    "table": """
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
    """,

    # List all user-created views and materialized views
    "view": """
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
    """,
    
    # Lists user-created functions, excluding those from extensions
    # Aggregate functions dont have a typical function body
    "function": """
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
    left join pg_catalog.pg_extension e
        on p.pronamespace = e.extnamespace
    where 
        n.nspname not in ('pg_catalog', 'information_schema')
        and e.extname is null
    order by n.nspname, p.proname;
    """
}

# Detailed queries provide in-depth information about specific object types
DETAIL_QUERIES = {
    "table": """
    select
        t.schemaname as schema,
        t.tablename as table_name,
        t.tableowner as owner,
        c.column_name,
        c.data_type,
        c.is_nullable,
        c.column_default,
        c.ordinal_position 
    from pg_catalog.pg_tables t
    join information_schema.columns c 
        on t.schemaname = c.table_schema 
        and t.tablename = c.table_name
    where t.schemaname not in ('pg_catalog', 'information_schema')
    order by 
        t.schemaname, 
        t.tablename, 
        c.ordinal_position;
    """
}