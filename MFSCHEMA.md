# Mutual Fund Database Schema Documentation

**Database:** `mutual_fund_db`  
**Source API:** https://apis.mfapis.in/api/v1/scheme/list/all  
**Engine:** PostgreSQL 12+  
**Character Set:** UTF8  

---

## 🗄️ **Database Overview**

### **Purpose**
Comprehensive mutual fund database storing complete scheme data, BSE trading details, returns history, and performance analytics from the mfapis.in API endpoint.

### **Database Statistics**
- **Total Schemes:** 1,488 mutual fund schemes
- **BSE Details:** 2,891 trading records  
- **Returns Records:** 9,827 performance data points
- **Total Records:** ~14,000+ across all tables
- **Database Size:** ~50MB
- **Processing Time:** 0.1 minutes (API fetch + import)

### **Key Features**
- ✅ Complete scheme metadata with AMFI classifications
- ✅ Normalized BSE trading information 
- ✅ Time-series returns data (1 day to 10 years)
- ✅ JSONB fields for flexible data storage
- ✅ Comprehensive indexing for performance
- ✅ Analysis views for quick insights
- ✅ Real-time NAV and AUM data

---

## 📊 **Table Structure**

### **Table 1: `schemes`**

**Purpose:** Main table containing comprehensive mutual fund scheme information

**Row Count:** 1,488 records  
**Primary Key:** `id`  
**Storage Engine:** PostgreSQL  

| Column Name | Data Type | Max Length | Nullable | Default | Constraints | Description | Sample Values |
|-------------|-----------|------------|----------|---------|-------------|-------------|---------------|
| `id` | VARCHAR | 50 | NOT NULL | - | PRIMARY KEY | Unique API identifier for the scheme | 'sch_01JWVNGBX9CQGF2SG93J4EQFV0' |
| `scheme_code` | VARCHAR | 20 | NOT NULL | - | UNIQUE | Numerical scheme code used across APIs | '105823', '149140', '140328' |
| `scheme_name` | TEXT | Variable | NOT NULL | - | - | Full official name of the mutual fund scheme | 'LIC MF Banking & PSU Fund Growth' |
| `amfi_broad` | VARCHAR | 50 | YES | NULL | - | AMFI broad category classification | 'Equity', 'Debt', 'Hybrid', 'Other' |
| `amfi_sub` | VARCHAR | 100 | YES | NULL | - | AMFI sub-category detailed classification | 'Banking and PSU Fund', 'Sectoral / Thematic' |
| `aum_in_lakhs` | DECIMAL | (20,2) | YES | NULL | - | Assets Under Management in Indian Lakhs | 196049.8, 58228.28, 12140.44 |
| `sip_allowed` | BOOLEAN | - | YES | FALSE | - | Whether Systematic Investment Plan is permitted | true, false |
| `purchase_allowed` | BOOLEAN | - | YES | FALSE | - | Whether direct purchase transactions are allowed | true, false |
| `risk_level` | INTEGER | - | YES | NULL | - | Investment risk rating (1-5 scale) | 1, 2, 3, 4, 5 |
| `amc_code` | VARCHAR | 50 | YES | NULL | - | Asset Management Company identifier code | 'LICMUTUALFUND_MF', 'BARODABNPPARIBASMUTUALFUND_MF' |
| `current_nav` | DECIMAL | (15,6) | YES | NULL | - | Current Net Asset Value per unit | 34.9318, 15.7556, 17.2871 |
| `amc_img_url` | TEXT | Variable | YES | NULL | - | URL to AMC logo/image | 'https://example.com/logo.png' |
| `returns_data` | JSONB | Variable | YES | NULL | - | Complete returns data in JSON format | `{"1d": -0.05, "1m": 0.03, "1y": 9.23}` |
| `sharpe_ratios` | JSONB | Variable | YES | NULL | - | Sharpe ratios for risk-adjusted returns | `{"3y": 1.25, "5y": 1.18}` |
| `nav_history` | JSONB | Variable | YES | NULL | - | Historical NAV data array | `[{"date": "2024-01-01", "nav": 34.93}]` |
| `created_at` | TIMESTAMP | - | NO | CURRENT_TIMESTAMP | - | Record creation timestamp | '2025-06-27 21:59:21' |
| `updated_at` | TIMESTAMP | - | NO | CURRENT_TIMESTAMP | - | Record last update timestamp | '2025-06-27 21:59:21' |

**Indexes:**
```sql
CREATE INDEX idx_schemes_code ON schemes(scheme_code);
CREATE INDEX idx_schemes_amfi_broad ON schemes(amfi_broad);
CREATE INDEX idx_schemes_amfi_sub ON schemes(amfi_sub);
CREATE INDEX idx_schemes_risk_level ON schemes(risk_level);
CREATE INDEX idx_schemes_amc_code ON schemes(amc_code);
CREATE INDEX idx_schemes_aum ON schemes(aum_in_lakhs DESC);
CREATE INDEX idx_schemes_nav ON schemes(current_nav);
```

---

### **Table 2: `bse_details`**

**Purpose:** Normalized BSE (Bombay Stock Exchange) trading information for each scheme

**Row Count:** 2,891 records  
**Primary Key:** `id`  
**Foreign Keys:** `scheme_id` → `schemes.id`  

| Column Name | Data Type | Max Length | Nullable | Default | Constraints | Description | Sample Values |
|-------------|-----------|------------|----------|---------|-------------|-------------|---------------|
| `id` | SERIAL | - | NOT NULL | AUTO_INCREMENT | PRIMARY KEY | Auto-incrementing unique identifier | 1, 2, 3... |
| `scheme_id` | VARCHAR | 50 | NOT NULL | - | FOREIGN KEY | References schemes.id | 'sch_01JWVNGBX9CQGF2SG93J4EQFV0' |
| `bse_code` | VARCHAR | 20 | YES | NULL | - | BSE trading code for the scheme | 'LCLPGP-GR', 'BPBCGP-GR' |
| `sip_flag` | BOOLEAN | - | YES | NULL | - | Whether SIP is available through BSE | true, false |
| `stp_flag` | BOOLEAN | - | YES | NULL | - | Whether STP (Systematic Transfer Plan) is available | true, false |
| `swp_flag` | BOOLEAN | - | YES | NULL | - | Whether SWP (Systematic Withdrawal Plan) is available | true, false |
| `switch_flag` | BOOLEAN | - | YES | NULL | - | Whether switching between schemes is allowed | true, false |
| `lock_in_flag` | BOOLEAN | - | YES | NULL | - | Whether the scheme has a lock-in period | true, false |
| `lock_in_period_months` | INTEGER | - | YES | NULL | - | Lock-in period duration in months | 36, 60, 12 |
| `exit_load_flag` | BOOLEAN | - | YES | NULL | - | Whether exit load is applicable | true, false |
| `exit_load_message` | TEXT | Variable | YES | NULL | - | Details about exit load conditions | 'NIL', '1% if redeemed within 1 year' |
| `purchase_allowed` | BOOLEAN | - | YES | NULL | - | Whether fresh purchases are allowed | true, false |
| `purchase_fresh_min` | DECIMAL | (15,2) | YES | NULL | - | Minimum amount for fresh purchase | 500.00, 1000.00, 5000.00 |
| `purchase_additional_min` | DECIMAL | (15,2) | YES | NULL | - | Minimum amount for additional purchase | 100.00, 500.00, 1000.00 |
| `purchase_max` | DECIMAL | (15,2) | YES | NULL | - | Maximum purchase amount allowed | 999999999.00, 1000000.00 |
| `purchase_delta` | DECIMAL | (15,2) | YES | NULL | - | Purchase amount increment/delta | 1.00, 100.00, 500.00 |
| `redemption_allowed` | BOOLEAN | - | YES | NULL | - | Whether redemptions are allowed | true, false |
| `redemption_min_amount` | DECIMAL | (15,2) | YES | NULL | - | Minimum redemption amount | 500.00, 1000.00 |
| `redemption_max_amount` | DECIMAL | (15,2) | YES | NULL | - | Maximum redemption amount | 999999999.00 |
| `redemption_min_quantity` | DECIMAL | (15,2) | YES | NULL | - | Minimum redemption quantity/units | 0.001, 1.000 |
| `redemption_max_quantity` | DECIMAL | (15,2) | YES | NULL | - | Maximum redemption quantity/units | 999999999.000 |
| `sip_dates` | TEXT | Variable | YES | NULL | - | Available SIP dates (comma-separated) | '1,5,10,15,20,25', 'Daily' |
| `sip_min_amount` | DECIMAL | (15,2) | YES | NULL | - | Minimum SIP amount | 100.00, 500.00, 1000.00 |
| `sip_max_amount` | DECIMAL | (15,2) | YES | NULL | - | Maximum SIP amount | 999999999.00, 100000.00 |
| `sip_delta_amount` | DECIMAL | (15,2) | YES | NULL | - | SIP amount increment/delta | 1.00, 100.00, 500.00 |
| `sip_min_installments` | INTEGER | - | YES | NULL | - | Minimum number of SIP installments | 6, 12, 24 |
| `sip_max_installments` | INTEGER | - | YES | NULL | - | Maximum number of SIP installments | 999, 240, 120 |
| `daily_sip_min_amount` | DECIMAL | (15,2) | YES | NULL | - | Minimum daily SIP amount | 100.00, 500.00 |
| `daily_sip_max_amount` | DECIMAL | (15,2) | YES | NULL | - | Maximum daily SIP amount | 50000.00, 100000.00 |
| `daily_sip_min_installments` | INTEGER | - | YES | NULL | - | Minimum daily SIP installments | 30, 60, 90 |
| `daily_sip_max_installments` | INTEGER | - | YES | NULL | - | Maximum daily SIP installments | 999, 365, 730 |
| `created_at` | TIMESTAMP | - | NO | CURRENT_TIMESTAMP | - | Record creation timestamp | '2025-06-27 21:59:21' |

**Indexes:**
```sql
CREATE INDEX idx_bse_scheme_id ON bse_details(scheme_id);
CREATE INDEX idx_bse_code ON bse_details(bse_code);
```

**Constraints:**
```sql
FOREIGN KEY (scheme_id) REFERENCES schemes(id) ON DELETE CASCADE
```

---

### **Table 3: `returns_history`**

**Purpose:** Time-series returns data for performance analysis across different periods

**Row Count:** 9,827 records  
**Primary Key:** `id`  
**Foreign Keys:** `scheme_id` → `schemes.id`  

| Column Name | Data Type | Max Length | Nullable | Default | Constraints | Description | Sample Values |
|-------------|-----------|------------|----------|---------|-------------|-------------|---------------|
| `id` | SERIAL | - | NOT NULL | AUTO_INCREMENT | PRIMARY KEY | Auto-incrementing unique identifier | 1, 2, 3... |
| `scheme_id` | VARCHAR | 50 | NOT NULL | - | FOREIGN KEY | References schemes.id | 'sch_01JWVNGBX9CQGF2SG93J4EQFV0' |
| `period` | VARCHAR | 10 | NOT NULL | - | - | Return calculation period | '1d', '1m', '6m', '1y', '3y', '5y', '10y' |
| `return_value` | DECIMAL | (8,4) | YES | NULL | - | Return percentage for the period | -0.05, 9.23, 15.67, -2.34 |
| `data_date` | DATE | - | YES | CURRENT_DATE | - | Date when the return was calculated | '2025-06-27' |
| `created_at` | TIMESTAMP | - | NO | CURRENT_TIMESTAMP | - | Record creation timestamp | '2025-06-27 21:59:21' |

**Indexes:**
```sql
CREATE INDEX idx_returns_scheme_period ON returns_history(scheme_id, period);
CREATE INDEX idx_returns_period ON returns_history(period);
```

**Constraints:**
```sql
FOREIGN KEY (scheme_id) REFERENCES schemes(id) ON DELETE CASCADE;
UNIQUE(scheme_id, period, data_date);
```

---

## 📊 **Analysis Views**

### **View 1: `scheme_summary`**

**Purpose:** Comprehensive scheme overview with aggregated counts and key metrics

**Based On:** JOIN between `schemes`, `bse_details`, and `returns_history` tables

| Column Name | Data Type | Description | Sample Values |
|-------------|-----------|-------------|---------------|
| `id` | VARCHAR(50) | Scheme unique identifier | 'sch_01JWVNGBX9CQGF2SG93J4EQFV0' |
| `scheme_code` | VARCHAR(20) | Numerical scheme code | '105823', '149140' |
| `scheme_name` | TEXT | Full scheme name | 'LIC MF Banking & PSU Fund Growth' |
| `amfi_broad` | VARCHAR(50) | Broad fund category | 'Equity', 'Debt', 'Hybrid' |
| `amfi_sub` | VARCHAR(100) | Sub-category classification | 'Banking and PSU Fund', 'Large Cap' |
| `amc_code` | VARCHAR(50) | Asset Management Company | 'LICMUTUALFUND_MF' |
| `current_nav` | DECIMAL(15,6) | Current NAV | 34.931800 |
| `aum_in_lakhs` | DECIMAL(20,2) | Assets Under Management | 196049.80 |
| `risk_level` | INTEGER | Risk rating (1-5) | 1, 2, 3, 4, 5 |
| `sip_allowed` | BOOLEAN | SIP availability | true, false |
| `purchase_allowed` | BOOLEAN | Purchase availability | true, false |
| `bse_options_count` | BIGINT | Number of BSE trading options | 1, 2, 3 |
| `returns_periods_count` | BIGINT | Number of return periods available | 5, 7, 9 |

**SQL Definition:**
```sql
CREATE OR REPLACE VIEW scheme_summary AS
SELECT 
    s.id,
    s.scheme_code,
    s.scheme_name,
    s.amfi_broad,
    s.amfi_sub,
    s.amc_code,
    s.current_nav,
    s.aum_in_lakhs,
    s.risk_level,
    s.sip_allowed,
    s.purchase_allowed,
    COUNT(b.id) as bse_options_count,
    COUNT(r.id) as returns_periods_count
FROM schemes s
LEFT JOIN bse_details b ON s.id = b.scheme_id
LEFT JOIN returns_history r ON s.id = r.scheme_id
GROUP BY s.id, s.scheme_code, s.scheme_name, s.amfi_broad, 
         s.amfi_sub, s.amc_code, s.current_nav, s.aum_in_lakhs, 
         s.risk_level, s.sip_allowed, s.purchase_allowed;
```

---

### **View 2: `top_performers`**

**Purpose:** Best performing schemes ranked by returns across different time periods

**Based On:** JOIN between `schemes` and `returns_history` tables

| Column Name | Data Type | Description | Sample Values |
|-------------|-----------|-------------|---------------|
| `scheme_name` | TEXT | Full scheme name | 'HDFC Large Cap Fund Growth' |
| `amfi_broad` | VARCHAR(50) | Broad fund category | 'Equity', 'Debt' |
| `amc_code` | VARCHAR(50) | Asset Management Company | 'HDFCMUTUALF' |
| `current_nav` | DECIMAL(15,6) | Current NAV | 245.670000 |
| `aum_in_lakhs` | DECIMAL(20,2) | Assets Under Management | 1234567.89 |
| `return_1y` | DECIMAL(8,4) | 1-year return percentage | 15.67, 12.34, 9.87 |
| `return_3y` | DECIMAL(8,4) | 3-year return percentage | 18.45, 14.23, 11.56 |
| `return_5y` | DECIMAL(8,4) | 5-year return percentage | 16.78, 13.45, 10.23 |

**SQL Definition:**
```sql
CREATE OR REPLACE VIEW top_performers AS
SELECT 
    s.scheme_name,
    s.amfi_broad,
    s.amc_code,
    s.current_nav,
    s.aum_in_lakhs,
    r1y.return_value as return_1y,
    r3y.return_value as return_3y,
    r5y.return_value as return_5y
FROM schemes s
LEFT JOIN returns_history r1y ON s.id = r1y.scheme_id AND r1y.period = '1y'
LEFT JOIN returns_history r3y ON s.id = r3y.scheme_id AND r3y.period = '3y'
LEFT JOIN returns_history r5y ON s.id = r5y.scheme_id AND r5y.period = '5y'
WHERE r1y.return_value IS NOT NULL
ORDER BY r1y.return_value DESC;
```

---

### **View 3: `category_performance`**

**Purpose:** Category-wise performance analysis and aggregated statistics

**Based On:** JOIN between `schemes` and `returns_history` tables with aggregation

| Column Name | Data Type | Description | Sample Values |
|-------------|-----------|-------------|---------------|
| `amfi_broad` | VARCHAR(50) | Broad fund category | 'Equity', 'Debt', 'Hybrid' |
| `amfi_sub` | VARCHAR(100) | Sub-category classification | 'Large Cap', 'Banking and PSU Fund' |
| `scheme_count` | BIGINT | Number of schemes in category | 512, 326, 169 |
| `avg_nav` | NUMERIC | Average NAV across category | 125.45, 89.67, 156.78 |
| `total_aum` | NUMERIC | Total AUM for category (in Lakhs) | 33361074.00, 15678234.50 |
| `avg_return_1y` | NUMERIC | Average 1-year return | 12.34, 8.76, 15.23 |
| `avg_return_3y` | NUMERIC | Average 3-year return | 14.56, 9.87, 16.45 |
| `avg_return_5y` | NUMERIC | Average 5-year return | 13.78, 8.45, 15.67 |
| `avg_risk_level` | NUMERIC | Average risk level | 3.5, 2.1, 4.2 |

**SQL Definition:**
```sql
CREATE OR REPLACE VIEW category_performance AS
SELECT 
    s.amfi_broad,
    s.amfi_sub,
    COUNT(*) as scheme_count,
    AVG(s.current_nav) as avg_nav,
    SUM(s.aum_in_lakhs) as total_aum,
    AVG(r1y.return_value) as avg_return_1y,
    AVG(r3y.return_value) as avg_return_3y,
    AVG(r5y.return_value) as avg_return_5y,
    AVG(s.risk_level) as avg_risk_level
FROM schemes s
LEFT JOIN returns_history r1y ON s.id = r1y.scheme_id AND r1y.period = '1y'
LEFT JOIN returns_history r3y ON s.id = r3y.scheme_id AND r3y.period = '3y'
LEFT JOIN returns_history r5y ON s.id = r5y.scheme_id AND r5y.period = '5y'
WHERE s.amfi_broad IS NOT NULL
GROUP BY s.amfi_broad, s.amfi_sub
ORDER BY avg_return_1y DESC NULLS LAST;
```

---

### **Table 4: `historical_nav_data`**

**Purpose:** Historical NAV data stored in JSONB array format for time-series analysis

**Row Count:** Variable (1 record per scheme with NAV history)  
**Primary Key:** `id`  
**Foreign Keys:** `scheme_id` → `schemes.id`  

| Column Name | Data Type | Max Length | Nullable | Default | Constraints | Description | Sample Values |
|-------------|-----------|------------|----------|---------|-------------|-------------|---------------|
| `id` | SERIAL | - | NOT NULL | AUTO_INCREMENT | PRIMARY KEY | Auto-incrementing unique identifier | 1, 2, 3... |
| `scheme_id` | VARCHAR | 50 | NOT NULL | - | FOREIGN KEY, UNIQUE | References schemes.id (one record per scheme) | 'sch_01JWVNGBX9CQGF2SG93J4EQFV0' |
| `scheme_code` | VARCHAR | 20 | NOT NULL | - | - | Scheme code for easy reference and validation | '105823', '149140', '140328' |
| `nav_history` | JSONB | Variable | NOT NULL | - | - | Array of date-wise NAV records in JSON format | `[{"date": "2024-01-01", "nav": 123.45}, {"date": "2024-01-02", "nav": 124.12}]` |
| `data_start_date` | DATE | - | YES | NULL | - | Earliest date in the NAV history array | '2020-01-01', '2018-06-15' |
| `data_end_date` | DATE | - | YES | NULL | - | Latest date in the NAV history array | '2024-12-31', '2024-08-30' |
| `total_records` | INTEGER | - | YES | 0 | CHECK (total_records >= 0) | Count of NAV records in the history array | 1250, 2100, 890 |
| `last_updated` | TIMESTAMP | - | YES | CURRENT_TIMESTAMP | - | When this record was last updated | '2025-08-30 09:41:14' |
| `created_at` | TIMESTAMP | - | NO | CURRENT_TIMESTAMP | - | Record creation timestamp | '2025-08-30 09:41:14' |

**JSONB Structure for `nav_history`:**
```json
[
  {
    "date": "2024-01-01",
    "nav": 123.4567,
    "source": "api"
  },
  {
    "date": "2024-01-02", 
    "nav": 124.1234,
    "source": "api"
  }
]
```

**Indexes:**
```sql
CREATE INDEX idx_historical_nav_scheme_id ON historical_nav_data(scheme_id);
CREATE INDEX idx_historical_nav_scheme_code ON historical_nav_data(scheme_code);
CREATE INDEX idx_historical_nav_date_range ON historical_nav_data(data_start_date, data_end_date);
CREATE INDEX idx_historical_nav_updated ON historical_nav_data(last_updated);
CREATE INDEX idx_historical_nav_history_gin ON historical_nav_data USING GIN (nav_history);
```

**Constraints:**
```sql
FOREIGN KEY (scheme_id) REFERENCES schemes(id) ON DELETE CASCADE;
UNIQUE (scheme_id);
```

---

### **View 4: `historical_nav_summary`**

**Purpose:** Summary view of historical NAV data with key statistics and date ranges

**Based On:** JOIN between `historical_nav_data` and `schemes` tables

| Column Name | Data Type | Description | Sample Values |
|-------------|-----------|-------------|---------------|
| `scheme_id` | VARCHAR(50) | Scheme unique identifier | 'sch_01JWVNGBX9CQGF2SG93J4EQFV0' |
| `scheme_code` | VARCHAR(20) | Numerical scheme code | '105823', '149140' |
| `scheme_name` | TEXT | Full scheme name | 'LIC MF Banking & PSU Fund Growth' |
| `amc_code` | VARCHAR(50) | Asset Management Company | 'LICMUTUALFUND_MF' |
| `amfi_broad` | VARCHAR(50) | Broad fund category | 'Equity', 'Debt', 'Hybrid' |
| `amfi_sub` | VARCHAR(100) | Sub-category classification | 'Banking and PSU Fund', 'Large Cap' |
| `data_start_date` | DATE | Earliest NAV date available | '2020-01-01', '2018-06-15' |
| `data_end_date` | DATE | Latest NAV date available | '2024-12-31', '2024-08-30' |
| `total_records` | INTEGER | Number of NAV records | 1250, 2100, 890 |
| `last_updated` | TIMESTAMP | Last data update timestamp | '2025-08-30 09:41:14' |
| `current_nav` | DECIMAL(15,6) | Current NAV from schemes table | 34.931800 |
| `aum_in_lakhs` | DECIMAL(20,2) | Assets Under Management | 196049.80 |
| `history_span_days` | INTEGER | Date range span in days | 1825, 2190, 1095 |
| `latest_historical_nav` | DECIMAL(15,6) | Latest NAV from history array | 34.931800 |
| `oldest_historical_nav` | DECIMAL(15,6) | Oldest NAV from history array | 28.456700 |

**SQL Definition:**
```sql
CREATE OR REPLACE VIEW historical_nav_summary AS
SELECT 
    h.scheme_id,
    h.scheme_code,
    s.scheme_name,
    s.amc_code,
    s.amfi_broad,
    s.amfi_sub,
    h.data_start_date,
    h.data_end_date,
    h.total_records,
    h.last_updated,
    s.current_nav,
    s.aum_in_lakhs,
    (h.data_end_date - h.data_start_date) as history_span_days,
    (h.nav_history->-1->>'nav')::DECIMAL(15,6) as latest_historical_nav,
    (h.nav_history->0->>'nav')::DECIMAL(15,6) as oldest_historical_nav
FROM historical_nav_data h
JOIN schemes s ON h.scheme_id = s.id
ORDER BY h.total_records DESC;
```

---

## 🔧 **Utility Functions**

### **Function 1: `get_nav_for_date(scheme_id, date)`**
**Purpose:** Retrieve NAV value for a specific scheme on a specific date
**Returns:** DECIMAL(15,6) - NAV value or NULL if not found

**Usage:**
```sql
SELECT get_nav_for_date('sch_01JWVNGBX9CQGF2SG93J4EQFV0', '2024-01-15');
```

### **Function 2: `get_nav_history_range(scheme_id, start_date, end_date)`**
**Purpose:** Get NAV history for a scheme within a date range
**Returns:** TABLE(nav_date DATE, nav_value DECIMAL(15,6))

**Usage:**
```sql
SELECT * FROM get_nav_history_range('sch_01JWVNGBX9CQGF2SG93J4EQFV0', '2024-01-01', '2024-01-31');
```

### **Function 3: `calculate_nav_return(scheme_id, start_date, end_date)`**
**Purpose:** Calculate return percentage between two dates
**Returns:** DECIMAL(8,4) - Return percentage

**Usage:**
```sql
SELECT calculate_nav_return('sch_01JWVNGBX9CQGF2SG93J4EQFV0', '2024-01-01', '2024-12-31');
```

---

## 🔗 **Relationships and Foreign Keys**

### **Database Relationships:**
```
schemes (1) ←→ (N) bse_details
  id ←→ scheme_id

schemes (1) ←→ (N) returns_history  
  id ←→ scheme_id

schemes (1) ←→ (1) historical_nav_data
  id ←→ scheme_id
```

### **Referential Integrity:**
- All foreign key relationships enforced with `CASCADE DELETE`
- Orphaned records automatically cleaned up when parent scheme is deleted
- Composite unique constraints prevent duplicate return data for same scheme/period/date

---

## 📋 **Data Quality Constraints**

### **Data Validation Rules:**
- `scheme_code` must be unique across all schemes
- `risk_level` must be between 1 and 5 (if specified)
- `return_value` can be negative (losses) or positive (gains)
- All monetary values use DECIMAL for precision
- `aum_in_lakhs` must be non-negative
- `current_nav` must be positive (if specified)
- Text fields are cleaned and limited to prevent overflow

### **JSONB Field Validation:**
- `returns_data` contains structured return periods as key-value pairs
- `sharpe_ratios` contains risk-adjusted return metrics
- `nav_history` contains array of historical NAV data points
- All JSONB fields are optional and can be NULL

---

## 🚀 **Performance Optimizations**

### **Indexing Strategy:**
- **Primary Keys:** Automatic B-tree indexes for fast lookups
- **Foreign Keys:** B-tree indexes for efficient JOIN operations  
- **Search Fields:** Indexes on frequently queried columns (amfi_broad, amc_code)
- **Sorting Fields:** Descending indexes for AUM and NAV sorting
- **Composite Indexes:** Multi-column indexes for complex queries

### **Query Performance:**
- Views pre-aggregate common analytical queries
- JSONB indexes can be added for specific JSON path queries
- Statistics updated regularly for optimal query planning
- Batch operations used for data imports

---

## 📊 **Data Distribution Statistics**

### **Schemes by Category:**
1. **Equity:** 512 schemes (34.4%) - ₹33,36,10,74L AUM
2. **Other:** 440 schemes (29.5%) - Mixed categories
3. **Debt:** 326 schemes (22.0%) - Fixed income funds  
4. **Hybrid:** 169 schemes (11.4%) - Mixed asset allocation
5. **Solution Oriented:** 41 schemes (2.7%) - Specialized funds

### **Returns Data Coverage:**
- **1-day returns:** Available for most active schemes
- **1-year returns:** Available for 80%+ schemes
- **3-year returns:** Available for 70%+ schemes  
- **5-year returns:** Available for 60%+ schemes
- **10-year returns:** Available for 40%+ schemes

### **BSE Trading Options:**
- **Average BSE options per scheme:** 1.9
- **SIP enabled schemes:** 85%+ of total schemes
- **Purchase enabled schemes:** 90%+ of total schemes
- **Lock-in period schemes:** 15% (mainly ELSS funds)

---

## 🔍 **API Integration Details**

### **Data Source:**
```
API Endpoint: https://apis.mfapis.in/api/v1/scheme/list/all
Method: GET
Response Format: JSON
Update Frequency: Real-time (on-demand)
Rate Limits: Standard API limits apply
```

### **Data Processing:**
- Automatic text cleaning for database compatibility
- Safe type conversion with error handling
- JSONB storage for flexible nested data
- Batch processing for optimal performance
- Comprehensive error logging and recovery

---

## 🛠️ **Usage Examples**

### **Connection String:**
```bash
psql -h localhost -U username -d mutual_fund_db
```

### **Common Queries:**

**1. Top performing equity funds:**
```sql
SELECT * FROM top_performers 
WHERE amfi_broad = 'Equity' 
ORDER BY return_1y DESC 
LIMIT 10;
```

**2. Schemes with highest AUM:**
```sql
SELECT scheme_name, amc_code, aum_in_lakhs, current_nav 
FROM schemes 
WHERE aum_in_lakhs IS NOT NULL 
ORDER BY aum_in_lakhs DESC 
LIMIT 10;
```

**3. Category-wise performance summary:**
```sql
SELECT * FROM category_performance 
ORDER BY scheme_count DESC;
```

**4. SIP-enabled schemes with low minimum amounts:**
```sql
SELECT s.scheme_name, s.amc_code, b.sip_min_amount 
FROM schemes s 
JOIN bse_details b ON s.id = b.scheme_id 
WHERE s.sip_allowed = true 
AND b.sip_min_amount <= 500 
ORDER BY b.sip_min_amount;
```

**5. JSONB queries for returns data:**
```sql
SELECT scheme_name, 
       returns_data->>'1y' as return_1y,
       returns_data->>'3y' as return_3y
FROM schemes 
WHERE returns_data IS NOT NULL 
AND (returns_data->>'1y')::numeric > 15;
```

---

## 🔧 **Maintenance and Updates**

### **Data Refresh:**
- Run `setup_updated_mutual_fund_db.py` to refresh all data
- Incremental updates possible by modifying the script
- Automatic conflict resolution with UPSERT operations
- Data validation and cleaning during import

### **Schema Evolution:**
- Add new columns with ALTER TABLE statements
- JSONB fields provide flexibility for new API fields
- Views can be updated without affecting base tables
- Indexes can be added/modified based on query patterns

### **Backup and Recovery:**
```bash
# Backup
pg_dump -h localhost -U username mutual_fund_db > backup.sql

# Restore  
psql -h localhost -U username -d mutual_fund_db < backup.sql
```

---

**Last Updated:** June 2025  
**Schema Version:** 1.0  
**Compatible With:** PostgreSQL 12+  
**API Version:** mfapis.in v1  
**Maintenance:** Automated via setup scripts
