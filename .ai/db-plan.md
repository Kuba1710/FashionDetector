# PostgreSQL Database Schema for FashionDetector MVP

## 1. Tables

### 1.1 `attribute_recognitions`
Tracks recognized clothing attributes from image analysis.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | SERIAL | PRIMARY KEY | Unique identifier for each record |
| timestamp | TIMESTAMP | NOT NULL | Time when the attribute was recognized |
| attribute_name | VARCHAR(50) | NOT NULL | Name of the attribute (color, pattern, cut, brand) |
| attribute_value | VARCHAR(100) | NOT NULL | Value of the recognized attribute |
| counter | INTEGER | NOT NULL DEFAULT 1 | Count of occurrences of this attribute |
| search_time_ms | INTEGER | DEFAULT NULL | Time taken to process in milliseconds |

```sql
CREATE TABLE attribute_recognitions (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    attribute_name VARCHAR(50) NOT NULL,
    attribute_value VARCHAR(100) NOT NULL,
    counter INTEGER NOT NULL DEFAULT 1,
    search_time_ms INTEGER DEFAULT NULL
);

-- Create an enum type for common attribute types to enforce consistency
CREATE TYPE attribute_type AS ENUM ('color', 'pattern', 'cut', 'brand');
ALTER TABLE attribute_recognitions ALTER COLUMN attribute_name TYPE attribute_type USING attribute_name::attribute_type;
```

### 1.2 `store_searches`
Tracks which stores were searched and whether the search was successful.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | SERIAL | PRIMARY KEY | Unique identifier for each record |
| timestamp | TIMESTAMP | NOT NULL | Time when the search was performed |
| store_name | VARCHAR(100) | NOT NULL | Name of the store that was searched |
| search_performed | BOOLEAN | NOT NULL | Whether the search was successfully performed |
| response_time_ms | INTEGER | DEFAULT NULL | Response time in milliseconds |

```sql
CREATE TABLE store_searches (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    store_name VARCHAR(100) NOT NULL,
    search_performed BOOLEAN NOT NULL,
    response_time_ms INTEGER DEFAULT NULL
);
```

### 1.3 `search_metrics`
Aggregates search performance metrics.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | SERIAL | PRIMARY KEY | Unique identifier for each record |
| timestamp | TIMESTAMP | NOT NULL | Time when the search was performed |
| total_time_ms | INTEGER | NOT NULL | Total search time in milliseconds |
| analysis_time_ms | INTEGER | DEFAULT NULL | Time taken for image analysis |
| search_time_ms | INTEGER | DEFAULT NULL | Time taken for store searching |
| result_count | INTEGER | NOT NULL DEFAULT 0 | Number of results found |

```sql
CREATE TABLE search_metrics (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    total_time_ms INTEGER NOT NULL,
    analysis_time_ms INTEGER DEFAULT NULL,
    search_time_ms INTEGER DEFAULT NULL,
    result_count INTEGER NOT NULL DEFAULT 0
);
```

## 2. Materialized Views

### 2.1 `attribute_stats`
Aggregates statistics on recognized attributes.

```sql
CREATE MATERIALIZED VIEW attribute_stats AS
SELECT 
    attribute_name,
    attribute_value,
    COUNT(*) as recognition_count,
    AVG(search_time_ms) as avg_recognition_time_ms,
    date_trunc('day', timestamp) as day
FROM 
    attribute_recognitions
GROUP BY 
    attribute_name, attribute_value, date_trunc('day', timestamp);
```

### 2.2 `store_stats`
Aggregates statistics on store searches.

```sql
CREATE MATERIALIZED VIEW store_stats AS
SELECT 
    store_name,
    COUNT(*) as search_count,
    COUNT(CASE WHEN search_performed = TRUE THEN 1 END) as successful_search_count,
    AVG(response_time_ms) as avg_response_time_ms,
    date_trunc('day', timestamp) as day
FROM 
    store_searches
GROUP BY 
    store_name, date_trunc('day', timestamp);
```

### 2.3 `search_performance_stats`
Aggregates search performance metrics over time.

```sql
CREATE MATERIALIZED VIEW search_performance_stats AS
SELECT 
    date_trunc('day', timestamp) as day,
    COUNT(*) as search_count,
    AVG(total_time_ms) as avg_total_time_ms,
    MAX(total_time_ms) as max_total_time_ms,
    AVG(analysis_time_ms) as avg_analysis_time_ms,
    AVG(search_time_ms) as avg_search_time_ms,
    AVG(result_count) as avg_result_count,
    SUM(CASE WHEN result_count > 0 THEN 1 ELSE 0 END) as successful_search_count
FROM 
    search_metrics
GROUP BY 
    date_trunc('day', timestamp);
```

## 3. Indexes

```sql
-- Indexes for attribute_recognitions
CREATE INDEX idx_attribute_recognitions_timestamp ON attribute_recognitions(timestamp);
CREATE INDEX idx_attribute_recognitions_name ON attribute_recognitions(attribute_name);
CREATE INDEX idx_attribute_recognitions_value ON attribute_recognitions(attribute_value);
CREATE INDEX idx_attribute_recognitions_name_value ON attribute_recognitions(attribute_name, attribute_value);

-- Indexes for store_searches
CREATE INDEX idx_store_searches_timestamp ON store_searches(timestamp);
CREATE INDEX idx_store_searches_store_name ON store_searches(store_name);
CREATE INDEX idx_store_searches_performed ON store_searches(search_performed);

-- Indexes for search_metrics
CREATE INDEX idx_search_metrics_timestamp ON search_metrics(timestamp);
CREATE INDEX idx_search_metrics_total_time ON search_metrics(total_time_ms);
```

## 4. Refresh Policies for Materialized Views

```sql
-- Create a function to refresh materialized views
CREATE OR REPLACE FUNCTION refresh_materialized_views()
RETURNS void AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY attribute_stats;
    REFRESH MATERIALIZED VIEW CONCURRENTLY store_stats;
    REFRESH MATERIALIZED VIEW CONCURRENTLY search_performance_stats;
END;
$$ LANGUAGE plpgsql;

-- Create a scheduled job to refresh views daily (using pg_cron extension if available)
-- If pg_cron is not available, this would need to be scheduled externally
-- Example with pg_cron:
-- SELECT cron.schedule('0 1 * * *', 'SELECT refresh_materialized_views()');
```

## 5. Design Considerations

1. **Simplicity**: The schema is intentionally simple to align with the MVP requirements, focusing only on essential analytics data.

2. **Performance**: 
   - Indexes are created on frequently queried columns
   - Materialized views are used for aggregations to improve query performance
   - No complex relationships that could impact query performance

3. **Data Retention**:
   - No specific data retention policy is implemented in the schema
   - Data retention can be managed through periodic pruning of old records as requirements evolve

4. **Data Aggregation**:
   - Materialized views provide efficient access to aggregated data
   - Regular refresh ensures data is relatively up-to-date without impacting system performance

5. **Scalability**:
   - The schema supports horizontal scaling as the application grows
   - No dependencies between tables that would complicate sharding

6. **Future Extension**:
   - The schema can be easily extended to include additional metrics or features
   - New tables can be added for user accounts, favorites, etc. in future versions 