# Data Architecture Documentation
## Pokemon Ability Data Pipeline - Flip Technical Test

---

## 📊 Overview

This document describes the complete data architecture for ingesting Pokemon ability data from PokeAPI through Staging, Operational Data Store (ODS), and Data Warehouse environments.

---

## 🏗️ Architecture Layers

### 1. **DATA SOURCES**

#### PokeAPI (External Source)
- **Type**: RESTful API
- **Endpoint**: `https://pokeapi.co/api/v2/ability/{id}`
- **Format**: JSON
- **Rate Limit**: Free tier (no authentication required)
- **Data Volume**: ~300 abilities, growing over time

#### User Input
- **Source**: FastAPI POST endpoint
- **Format**: JSON payload with raw_id, user_id, pokemon_ability_id
- **Validation**: Pydantic models ensure data integrity

---

### 2. **STAGING LAYER**

**Purpose**: Landing zone for raw, unprocessed data

#### Table: `stg_pokemon_raw`
```sql
CREATE TABLE stg_pokemon_raw (
    staging_id BIGINT PRIMARY KEY AUTO_INCREMENT,
    raw_payload JSON NOT NULL,
    raw_id VARCHAR(13),
    user_id VARCHAR(7),
    ability_id INTEGER,
    ingestion_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    source_system VARCHAR(50) DEFAULT 'pokeapi',
    batch_id VARCHAR(50)
);
```

#### Table: `stg_api_logs`
```sql
CREATE TABLE stg_api_logs (
    log_id BIGINT PRIMARY KEY AUTO_INCREMENT,
    request_url VARCHAR(500),
    request_method VARCHAR(10),
    request_payload TEXT,
    response_status_code INTEGER,
    response_payload TEXT,
    response_time_ms INTEGER,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    error_message TEXT
);
```

**Characteristics**:
- ✅ Append-only (no updates/deletes)
- ✅ Complete API response stored as-is
- ✅ Audit trail for all API calls
- ✅ Retention: 90 days
- ✅ No business logic applied

**ETL Process**:
```python
# Pseudo-code for staging ingestion
def ingest_to_staging(api_response, metadata):
    staging_record = {
        'raw_payload': json.dumps(api_response),
        'raw_id': metadata['raw_id'],
        'user_id': metadata['user_id'],
        'ability_id': metadata['ability_id'],
        'batch_id': generate_batch_id()
    }
    staging_table.insert(staging_record)
```

---

### 3. **OPERATIONAL DATA STORE (ODS)**

**Purpose**: Current state of normalized, business-ready data

#### Core Tables

##### Table: `pokemon_abilities` (Current Implementation)
```sql
CREATE TABLE pokemon_abilities (
    id INTEGER PRIMARY KEY AUTO_INCREMENT,
    raw_id VARCHAR(13) NOT NULL,
    user_id VARCHAR(7) NOT NULL,
    pokemon_ability_id INTEGER NOT NULL,
    effect TEXT NOT NULL,
    language JSON NOT NULL,
    short_effect TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_raw_user (raw_id, user_id),
    INDEX idx_ability (pokemon_ability_id)
);
```

##### Table: `pokemon_master`
```sql
CREATE TABLE pokemon_master (
    pokemon_id INTEGER PRIMARY KEY,
    pokemon_name VARCHAR(100) NOT NULL UNIQUE,
    pokemon_url VARCHAR(200),
    is_hidden_ability BOOLEAN DEFAULT FALSE,
    slot INTEGER,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);
```

##### Table: `ability_master`
```sql
CREATE TABLE ability_master (
    ability_id INTEGER PRIMARY KEY,
    ability_name VARCHAR(100) NOT NULL UNIQUE,
    ability_url VARCHAR(200),
    generation_id INTEGER,
    is_main_series BOOLEAN DEFAULT TRUE,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);
```

##### Table: `language_master`
```sql
CREATE TABLE language_master (
    language_id INTEGER PRIMARY KEY,
    language_name VARCHAR(50) NOT NULL UNIQUE,
    language_code VARCHAR(10),
    language_url VARCHAR(200),
    iso639 VARCHAR(2),
    iso3166 VARCHAR(2)
);
```

##### Table: `ability_effect_entries`
```sql
CREATE TABLE ability_effect_entries (
    entry_id INTEGER PRIMARY KEY AUTO_INCREMENT,
    ability_id INTEGER NOT NULL,
    language_id INTEGER NOT NULL,
    effect TEXT,
    short_effect TEXT,
    FOREIGN KEY (ability_id) REFERENCES ability_master(ability_id),
    FOREIGN KEY (language_id) REFERENCES language_master(language_id),
    UNIQUE KEY unique_ability_language (ability_id, language_id)
);
```

**Characteristics**:
- ✅ Normalized to 3NF (Third Normal Form)
- ✅ Foreign key constraints enforced
- ✅ Supports CRUD operations
- ✅ Real-time updates
- ✅ Indexed for fast queries
- ✅ Retention: Based on business requirements

**ETL Process**: Staging → ODS
```python
def ods_etl_process():
    # Extract from staging
    staging_records = fetch_new_staging_records()
    
    for record in staging_records:
        api_data = json.loads(record.raw_payload)
        
        # Transform: Normalize ability data
        ability_data = normalize_ability(api_data)
        upsert_ability_master(ability_data)
        
        # Transform: Normalize pokemon data
        for pokemon in api_data['pokemon']:
            pokemon_data = normalize_pokemon(pokemon)
            upsert_pokemon_master(pokemon_data)
        
        # Transform: Normalize effect entries
        for entry in api_data['effect_entries']:
            effect_data = normalize_effect_entry(entry)
            upsert_effect_entry(effect_data)
        
        # Transform: Normalize language data
        for entry in api_data['effect_entries']:
            language_data = normalize_language(entry['language'])
            upsert_language_master(language_data)
        
        # Mark staging record as processed
        mark_as_processed(record.staging_id)
```

---

### 4. **DATA WAREHOUSE LAYER**

**Purpose**: Historical data for analytics and reporting

#### Dimensional Model (Star Schema)

##### Fact Table: `fact_ability_requests`
```sql
CREATE TABLE fact_ability_requests (
    request_key BIGINT PRIMARY KEY AUTO_INCREMENT,
    date_key INTEGER NOT NULL,
    user_key INTEGER NOT NULL,
    ability_key INTEGER NOT NULL,
    pokemon_key INTEGER,
    language_key INTEGER,
    
    -- Metrics
    request_count INTEGER DEFAULT 1,
    response_time_ms INTEGER,
    success_flag BOOLEAN,
    error_count INTEGER DEFAULT 0,
    
    -- Timestamps
    request_timestamp TIMESTAMP,
    
    FOREIGN KEY (date_key) REFERENCES dim_date(date_key),
    FOREIGN KEY (user_key) REFERENCES dim_user(user_key),
    FOREIGN KEY (ability_key) REFERENCES dim_ability(ability_key),
    FOREIGN KEY (pokemon_key) REFERENCES dim_pokemon(pokemon_key),
    FOREIGN KEY (language_key) REFERENCES dim_language(language_key),
    
    INDEX idx_date (date_key),
    INDEX idx_user (user_key),
    INDEX idx_ability (ability_key)
);
```

##### Fact Table: `fact_pokemon_usage`
```sql
CREATE TABLE fact_pokemon_usage (
    usage_key BIGINT PRIMARY KEY AUTO_INCREMENT,
    date_key INTEGER NOT NULL,
    pokemon_key INTEGER NOT NULL,
    ability_key INTEGER NOT NULL,
    
    -- Metrics
    query_count INTEGER DEFAULT 0,
    unique_users INTEGER DEFAULT 0,
    avg_response_time_ms DECIMAL(10,2),
    
    FOREIGN KEY (date_key) REFERENCES dim_date(date_key),
    FOREIGN KEY (pokemon_key) REFERENCES dim_pokemon(pokemon_key),
    FOREIGN KEY (ability_key) REFERENCES dim_ability(ability_key)
);
```

##### Dimension: `dim_pokemon` (SCD Type 2)
```sql
CREATE TABLE dim_pokemon (
    pokemon_key INTEGER PRIMARY KEY AUTO_INCREMENT,
    pokemon_id INTEGER NOT NULL,  -- Natural Key
    pokemon_name VARCHAR(100),
    pokemon_type_1 VARCHAR(50),
    pokemon_type_2 VARCHAR(50),
    generation INTEGER,
    is_legendary BOOLEAN DEFAULT FALSE,
    is_mythical BOOLEAN DEFAULT FALSE,
    
    -- SCD Type 2 columns
    valid_from DATE NOT NULL,
    valid_to DATE DEFAULT '9999-12-31',
    is_current BOOLEAN DEFAULT TRUE,
    
    INDEX idx_pokemon_id (pokemon_id),
    INDEX idx_current (is_current)
);
```

##### Dimension: `dim_ability` (SCD Type 2)
```sql
CREATE TABLE dim_ability (
    ability_key INTEGER PRIMARY KEY AUTO_INCREMENT,
    ability_id INTEGER NOT NULL,  -- Natural Key
    ability_name VARCHAR(100),
    ability_category VARCHAR(50),
    generation INTEGER,
    is_hidden BOOLEAN DEFAULT FALSE,
    
    -- SCD Type 2 columns
    valid_from DATE NOT NULL,
    valid_to DATE DEFAULT '9999-12-31',
    is_current BOOLEAN DEFAULT TRUE,
    
    INDEX idx_ability_id (ability_id),
    INDEX idx_current (is_current)
);
```

##### Dimension: `dim_user`
```sql
CREATE TABLE dim_user (
    user_key INTEGER PRIMARY KEY AUTO_INCREMENT,
    user_id VARCHAR(7) NOT NULL UNIQUE,  -- Natural Key
    registration_date DATE,
    user_segment VARCHAR(50),
    country_code VARCHAR(2),
    total_requests INTEGER DEFAULT 0,
    first_request_date DATE,
    last_request_date DATE
);
```

##### Dimension: `dim_date`
```sql
CREATE TABLE dim_date (
    date_key INTEGER PRIMARY KEY,  -- Format: YYYYMMDD
    date DATE NOT NULL UNIQUE,
    year INTEGER,
    quarter INTEGER,
    month INTEGER,
    month_name VARCHAR(20),
    week INTEGER,
    day_of_month INTEGER,
    day_of_week INTEGER,
    day_name VARCHAR(20),
    is_weekend BOOLEAN,
    is_holiday BOOLEAN,
    fiscal_year INTEGER,
    fiscal_quarter INTEGER
);
```

##### Dimension: `dim_language` (SCD Type 1)
```sql
CREATE TABLE dim_language (
    language_key INTEGER PRIMARY KEY AUTO_INCREMENT,
    language_id INTEGER NOT NULL UNIQUE,  -- Natural Key
    language_name VARCHAR(50),
    language_code VARCHAR(10),
    iso639 VARCHAR(2),
    iso3166 VARCHAR(2),
    is_official BOOLEAN DEFAULT TRUE
);
```

**Characteristics**:
- ✅ Star schema for optimal query performance
- ✅ Slowly Changing Dimensions (SCD) Type 1 & 2
- ✅ Pre-aggregated metrics
- ✅ Historical tracking
- ✅ Retention: 5+ years
- ✅ Daily batch loads

**ETL Process**: ODS → DWH
```python
def dwh_etl_process():
    # Daily batch job
    
    # 1. Update Dimensions
    sync_dim_pokemon()  # SCD Type 2
    sync_dim_ability()  # SCD Type 2
    sync_dim_user()     # SCD Type 1
    sync_dim_language() # SCD Type 1
    ensure_dim_date()   # Pre-populated
    
    # 2. Load Facts
    yesterday = get_yesterday_date()
    
    # Load ability request facts
    ability_requests = fetch_ods_requests(yesterday)
    for request in ability_requests:
        fact_record = {
            'date_key': get_date_key(request.timestamp),
            'user_key': lookup_user_key(request.user_id),
            'ability_key': lookup_ability_key(request.ability_id),
            'pokemon_key': lookup_pokemon_key(request.pokemon_id),
            'language_key': lookup_language_key(request.language_id),
            'request_count': 1,
            'response_time_ms': request.response_time,
            'success_flag': request.success
        }
        insert_fact_ability_request(fact_record)
    
    # Aggregate pokemon usage
    aggregate_pokemon_usage(yesterday)
```

---

## 🔄 ETL Schedule

| Job | Frequency | Duration | Description |
|-----|-----------|----------|-------------|
| Staging Ingestion | Real-time | < 1s | Capture raw API responses |
| Staging → ODS | Every 5 mins | 1-2 mins | Normalize and load to ODS |
| ODS → DWH | Daily (2 AM) | 30-60 mins | Load facts and update dimensions |
| Dimension Updates | Daily (1 AM) | 15-30 mins | SCD processing |
| Aggregations | Daily (3 AM) | 20-40 mins | Pre-calculate metrics |

---

## 📈 Data Flow Summary

```
API Request → FastAPI → Staging (Raw JSON)
                            ↓
                    Extract & Transform
                            ↓
                    ODS (Normalized Tables)
                            ↓
                    Aggregate & Historicize
                            ↓
                    DWH (Star Schema)
                            ↓
                    BI Tools & Reports
```

---

## 🎯 Design Principles

### 1. **Separation of Concerns**
- Staging: Raw data preservation
- ODS: Current operational state
- DWH: Historical analytics

### 2. **Data Quality**
- Schema validation at each layer
- Data type enforcement
- Referential integrity
- Deduplication logic

### 3. **Scalability**
- Horizontal scaling with partitioning
- Indexed for fast queries
- Batch processing for heavy loads

### 4. **Auditability**
- Complete audit trail in staging
- SCD Type 2 tracks historical changes
- Timestamps on all records

### 5. **Performance**
- Denormalized DWH for fast analytics
- Materialized aggregations
- Optimized indexes

---

## 🛠️ Technology Stack Recommendations

| Layer | Technology Options | Reasoning |
|-------|-------------------|-----------|
| **Staging** | S3 + Parquet, HDFS, PostgreSQL | Cheap storage, append-only |
| **ODS** | PostgreSQL, MySQL, SQL Server | ACID compliance, relational |
| **DWH** | Snowflake, Redshift, BigQuery | Columnar, fast analytics |
| **ETL** | Airflow, Prefect, dbt | Orchestration, scheduling |
| **BI** | Tableau, Power BI, Metabase | Visualization, dashboards |

---

## 📊 Sample Analytics Use Cases

### 1. **Pokemon Popularity Analysis**
```sql
SELECT 
    dp.pokemon_name,
    COUNT(DISTINCT f.user_key) as unique_users,
    COUNT(*) as total_requests,
    AVG(f.response_time_ms) as avg_response_time
FROM fact_ability_requests f
JOIN dim_pokemon dp ON f.pokemon_key = dp.pokemon_key
JOIN dim_date dd ON f.date_key = dd.date_key
WHERE dd.date >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)
    AND dp.is_current = TRUE
GROUP BY dp.pokemon_name
ORDER BY total_requests DESC
LIMIT 10;
```

### 2. **Ability Usage Trends**
```sql
SELECT 
    dd.month_name,
    dd.year,
    da.ability_name,
    SUM(f.request_count) as requests
FROM fact_ability_requests f
JOIN dim_date dd ON f.date_key = dd.date_key
JOIN dim_ability da ON f.ability_key = da.ability_key
WHERE da.is_current = TRUE
GROUP BY dd.year, dd.month_name, da.ability_name
ORDER BY dd.year, dd.month, requests DESC;
```

### 3. **API Performance Monitoring**
```sql
SELECT 
    dd.date,
    COUNT(*) as total_requests,
    AVG(f.response_time_ms) as avg_response_time,
    MAX(f.response_time_ms) as max_response_time,
    SUM(CASE WHEN f.success_flag = FALSE THEN 1 ELSE 0 END) as error_count
FROM fact_ability_requests f
JOIN dim_date dd ON f.date_key = dd.date_key
WHERE dd.date >= DATE_SUB(CURDATE(), INTERVAL 7 DAY)
GROUP BY dd.date
ORDER BY dd.date;
```

---

## 🔐 Data Governance

### Data Quality Rules
1. **Completeness**: No null values in required fields
2. **Validity**: Foreign keys must reference existing dimensions
3. **Accuracy**: API responses match expected schema
4. **Consistency**: Same ability always has same attributes
5. **Timeliness**: Data loaded within SLA windows

### Security & Privacy
- Role-based access control (RBAC)
- PII encryption for user data
- Audit logging for all access
- Data retention policies enforced

---

## 📝 Maintenance & Monitoring

### Daily Checks
- ✅ ETL job success/failure
- ✅ Data quality metrics
- ✅ Row counts validation
- ✅ API error rates

### Weekly Reviews
- ✅ Performance tuning
- ✅ Storage capacity planning
- ✅ Query optimization

### Monthly Tasks
- ✅ Archive old staging data
- ✅ Rebuild indexes
- ✅ Review partitioning strategy

---

## 🚀 Future Enhancements

1. **Real-time Streaming**: Kafka + Spark for real-time analytics
2. **Data Lake**: Store raw data in data lake (S3/ADLS)
3. **ML Integration**: Feature store for ML models
4. **Change Data Capture**: Real-time ODS → DWH sync
5. **Data Catalog**: Automated metadata management
6. **Data Lineage**: Track data flow end-to-end

---

**Document Version**: 1.0  
**Last Updated**: February 2026  
**Author**: Data Engineering Team
