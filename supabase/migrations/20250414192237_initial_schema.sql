-- migration: 20250414192237_initial_schema.sql
-- description: creates initial database schema for fashiondetector mvp
-- tables: attribute_recognitions, store_searches, search_metrics
-- views: attribute_stats, store_stats, search_performance_stats

-- this migration implements the core analytics schema for the fashiondetector application
-- the schema focuses on collecting minimal analytics data as specified in the project requirements

--------------------
-- attribute types
--------------------

-- create an enum type for common attribute types to enforce consistency
create type attribute_type as enum ('color', 'pattern', 'cut', 'brand');

--------------------
-- tables
--------------------

-- attribute_recognitions: tracks recognized clothing attributes from image analysis
create table attribute_recognitions (
    id serial primary key,
    timestamp timestamp not null default current_timestamp,
    attribute_name attribute_type not null,
    attribute_value varchar(100) not null,
    counter integer not null default 1,
    search_time_ms integer default null
);

-- enable row level security (rls)
alter table attribute_recognitions enable row level security;

-- store_searches: tracks which stores were searched and whether the search was successful
create table store_searches (
    id serial primary key,
    timestamp timestamp not null default current_timestamp,
    store_name varchar(100) not null,
    search_performed boolean not null,
    response_time_ms integer default null
);

-- enable row level security (rls)
alter table store_searches enable row level security;

-- search_metrics: aggregates search performance metrics
create table search_metrics (
    id serial primary key,
    timestamp timestamp not null default current_timestamp,
    total_time_ms integer not null,
    analysis_time_ms integer default null,
    search_time_ms integer default null,
    result_count integer not null default 0
);

-- enable row level security (rls)
alter table search_metrics enable row level security;

--------------------
-- indexes
--------------------

-- indexes for attribute_recognitions
create index idx_attribute_recognitions_timestamp on attribute_recognitions(timestamp);
create index idx_attribute_recognitions_name on attribute_recognitions(attribute_name);
create index idx_attribute_recognitions_value on attribute_recognitions(attribute_value);
create index idx_attribute_recognitions_name_value on attribute_recognitions(attribute_name, attribute_value);

-- indexes for store_searches
create index idx_store_searches_timestamp on store_searches(timestamp);
create index idx_store_searches_store_name on store_searches(store_name);
create index idx_store_searches_performed on store_searches(search_performed);

-- indexes for search_metrics
create index idx_search_metrics_timestamp on search_metrics(timestamp);
create index idx_search_metrics_total_time on search_metrics(total_time_ms);

--------------------
-- materialized views
--------------------

-- attribute_stats: aggregates statistics on recognized attributes
create materialized view attribute_stats as
select 
    attribute_name,
    attribute_value,
    count(*) as recognition_count,
    avg(search_time_ms) as avg_recognition_time_ms,
    date_trunc('day', timestamp) as day
from 
    attribute_recognitions
group by 
    attribute_name, attribute_value, date_trunc('day', timestamp);

-- store_stats: aggregates statistics on store searches
create materialized view store_stats as
select 
    store_name,
    count(*) as search_count,
    count(case when search_performed = true then 1 end) as successful_search_count,
    avg(response_time_ms) as avg_response_time_ms,
    date_trunc('day', timestamp) as day
from 
    store_searches
group by 
    store_name, date_trunc('day', timestamp);

-- search_performance_stats: aggregates search performance metrics over time
create materialized view search_performance_stats as
select 
    date_trunc('day', timestamp) as day,
    count(*) as search_count,
    avg(total_time_ms) as avg_total_time_ms,
    max(total_time_ms) as max_total_time_ms,
    avg(analysis_time_ms) as avg_analysis_time_ms,
    avg(search_time_ms) as avg_search_time_ms,
    avg(result_count) as avg_result_count,
    sum(case when result_count > 0 then 1 else 0 end) as successful_search_count
from 
    search_metrics
group by 
    date_trunc('day', timestamp);

--------------------
-- refresh function
--------------------

-- create a function to refresh materialized views
create or replace function refresh_materialized_views()
returns void as $$
begin
    refresh materialized view concurrently attribute_stats;
    refresh materialized view concurrently store_stats;
    refresh materialized view concurrently search_performance_stats;
end;
$$ language plpgsql;

--------------------
-- row level security policies
--------------------

-- attribute_recognitions table policies
-- policy for anon role: select access only
create policy "anon can view attribute_recognitions"
    on attribute_recognitions for select
    to anon
    using (true);

-- policy for authenticated role: select access only
create policy "authenticated can view attribute_recognitions"
    on attribute_recognitions for select
    to authenticated
    using (true);

-- policy for service_role: full access for internal system operations
create policy "service_role can manage attribute_recognitions"
    on attribute_recognitions for all
    to service_role
    using (true)
    with check (true);

-- store_searches table policies
-- policy for anon role: select access only
create policy "anon can view store_searches"
    on store_searches for select
    to anon
    using (true);

-- policy for authenticated role: select access only
create policy "authenticated can view store_searches"
    on store_searches for select
    to authenticated
    using (true);

-- policy for service_role: full access for internal system operations
create policy "service_role can manage store_searches"
    on store_searches for all
    to service_role
    using (true)
    with check (true);

-- search_metrics table policies
-- policy for anon role: select access only
create policy "anon can view search_metrics"
    on search_metrics for select
    to anon
    using (true);

-- policy for authenticated role: select access only
create policy "authenticated can view search_metrics"
    on search_metrics for select
    to authenticated
    using (true);

-- policy for service_role: full access for internal system operations
create policy "service_role can manage search_metrics"
    on search_metrics for all
    to service_role
    using (true)
    with check (true);

-- comment: data in these tables is intended to be public for analytics purposes
-- only the service_role is allowed to modify the data
-- this aligns with the project requirements where we're only storing anonymized analytics data 