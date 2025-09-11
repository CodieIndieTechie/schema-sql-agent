# Mutual Fund Database Schema Documentation

## Overview

The `mutual_fund` PostgreSQL database contains comprehensive mutual fund data from MF APIs Club with 6 interconnected tables storing 14,562+ records across 1,487 mutual fund schemes.

### Database Statistics
- **Total Schemes**: 1,487
- **Performance Records**: 1,486 
- **Sharpe Ratios**: 267
- **BSE Trading Details**: 2,889
- **SIP Configurations**: 3,961
- **Transaction Configs**: 5,778

### Data Source
- **API**: https://app.mfapis.club/api/v1/scheme/list
- **Update Frequency**: Real-time via API
- **Coverage**: All AMFI registered mutual funds

---

## Table Relationships

```
schemes (1:1) ← scheme_returns
schemes (1:1) ← sharpe_ratios  
schemes (1:M) → bse_details
bse_details (1:M) → sip_configurations
bse_details (1:M) → transaction_configurations
```

---

## 1. SCHEMES Table

**Purpose**: Core mutual fund information and metadata

| Column | Type | Description |
|--------|------|-------------|
| id | TEXT (PK) | Unique scheme identifier from MF APIs Club |
| scheme_code | TEXT (UNIQUE) | AMFI scheme code |
| scheme_name | TEXT | Full scheme name |
| amfi_broad | TEXT | Broad category (Equity, Debt, Hybrid, Other, Solution Oriented) |
| amfi_sub | TEXT | Sub-category (Large Cap Fund, Liquid Fund, etc.) |
| aum_in_lakhs | DECIMAL(15,2) | Assets Under Management in lakhs |
| current_nav | DECIMAL(10,6) | Latest Net Asset Value |
| risk_level | INTEGER | Risk rating 1-5 (1=lowest, 5=highest) |
| amc_code | TEXT | Asset Management Company code |
| amc_img_url | TEXT | AMC logo URL |
| sip_allowed | BOOLEAN | SIP investment allowed |
| purchase_allowed | BOOLEAN | Lump sum purchase allowed |
| created_at | TIMESTAMP | Record creation time |
| updated_at | TIMESTAMP | Last update time |

### Text-to-SQL Examples

**1. "Find all large cap equity funds with AUM greater than 1000 crores"**
```sql
SELECT scheme_name, aum_in_lakhs, current_nav, risk_level
FROM schemes 
WHERE amfi_broad = 'Equity' 
    AND amfi_sub = 'Large Cap Fund'
    AND aum_in_lakhs > 100000
ORDER BY aum_in_lakhs DESC;
```

**2. "Show me the top 10 schemes by AUM in each category"**
```sql
SELECT amfi_broad, scheme_name, aum_in_lakhs,
       ROW_NUMBER() OVER (PARTITION BY amfi_broad ORDER BY aum_in_lakhs DESC) as rank
FROM schemes
WHERE aum_in_lakhs IS NOT NULL
QUALIFY rank <= 10
ORDER BY amfi_broad, rank;
```

**3. "List all SIP-enabled debt funds with low risk (level 1-2)"**
```sql
SELECT scheme_name, amfi_sub, risk_level, current_nav, aum_in_lakhs
FROM schemes
WHERE amfi_broad = 'Debt'
    AND sip_allowed = true
    AND risk_level <= 2
ORDER BY aum_in_lakhs DESC;
```

**4. "Find schemes from HDFC AMC with current NAV between 10-50"**
```sql
SELECT scheme_name, amfi_sub, current_nav, aum_in_lakhs
FROM schemes
WHERE amc_code LIKE '%HDFC%'
    AND current_nav BETWEEN 10 AND 50
ORDER BY current_nav;
```

**5. "Show category-wise fund count and average AUM"**
```sql
SELECT amfi_broad, 
       COUNT(*) as fund_count,
       ROUND(AVG(aum_in_lakhs), 2) as avg_aum_lakhs,
       ROUND(AVG(current_nav), 4) as avg_nav
FROM schemes
GROUP BY amfi_broad
ORDER BY fund_count DESC;
```

---

## 2. SCHEME_RETURNS Table

**Purpose**: Performance returns across multiple time periods

| Column | Type | Description |
|--------|------|-------------|
| scheme_id | TEXT (PK, FK) | References schemes.id |
| days1 | DECIMAL(8,4) | 1-day return percentage |
| mths1 | DECIMAL(8,4) | 1-month return percentage |
| mths6 | DECIMAL(8,4) | 6-month return percentage |
| yrs1 | DECIMAL(8,4) | 1-year return percentage |
| yrs2 | DECIMAL(8,4) | 2-year return percentage |
| yrs3 | DECIMAL(8,4) | 3-year return percentage |
| yrs5 | DECIMAL(8,4) | 5-year return percentage |
| yrs7 | DECIMAL(8,4) | 7-year return percentage |
| yrs10 | DECIMAL(8,4) | 10-year return percentage |
| created_at | TIMESTAMP | Record creation time |

### Text-to-SQL Examples

**1. "Find top 10 performing equity funds over 5 years"**
```sql
SELECT s.scheme_name, s.amfi_sub, sr.yrs5, sr.yrs3, sr.yrs1
FROM schemes s
JOIN scheme_returns sr ON s.id = sr.scheme_id
WHERE s.amfi_broad = 'Equity' AND sr.yrs5 IS NOT NULL
ORDER BY sr.yrs5 DESC
LIMIT 10;
```

**2. "Show funds with consistent performance (positive returns across all periods)"**
```sql
SELECT s.scheme_name, s.amfi_broad, sr.yrs1, sr.yrs3, sr.yrs5
FROM schemes s
JOIN scheme_returns sr ON s.id = sr.scheme_id
WHERE sr.yrs1 > 0 AND sr.yrs3 > 0 AND sr.yrs5 > 0
ORDER BY (sr.yrs1 + sr.yrs3 + sr.yrs5) DESC;
```

**3. "Compare short-term vs long-term performance for hybrid funds"**
```sql
SELECT s.scheme_name, 
       sr.mths6 as short_term,
       sr.yrs5 as long_term,
       (sr.yrs5 - sr.mths6) as performance_difference
FROM schemes s
JOIN scheme_returns sr ON s.id = sr.scheme_id
WHERE s.amfi_broad = 'Hybrid'
    AND sr.mths6 IS NOT NULL 
    AND sr.yrs5 IS NOT NULL
ORDER BY performance_difference DESC;
```

**4. "Find funds with recent outperformance (1-month > 1-year average)"**
```sql
SELECT s.scheme_name, s.amfi_sub, sr.mths1, sr.yrs1,
       (sr.mths1 * 12) as annualized_recent
FROM schemes s
JOIN scheme_returns sr ON s.id = sr.scheme_id
WHERE sr.mths1 IS NOT NULL 
    AND sr.yrs1 IS NOT NULL
    AND (sr.mths1 * 12) > sr.yrs1
ORDER BY (sr.mths1 * 12 - sr.yrs1) DESC;
```

**5. "Calculate average returns by fund category and time period"**
```sql
SELECT s.amfi_broad,
       ROUND(AVG(sr.yrs1), 2) as avg_1yr,
       ROUND(AVG(sr.yrs3), 2) as avg_3yr,
       ROUND(AVG(sr.yrs5), 2) as avg_5yr,
       COUNT(*) as fund_count
FROM schemes s
JOIN scheme_returns sr ON s.id = sr.scheme_id
GROUP BY s.amfi_broad
ORDER BY avg_5yr DESC NULLS LAST;
```

---

## 3. SHARPE_RATIOS Table

**Purpose**: Risk-adjusted performance metrics

| Column | Type | Description |
|--------|------|-------------|
| scheme_id | TEXT (PK, FK) | References schemes.id |
| sharpe_3yr | DECIMAL(8,4) | 3-year Sharpe ratio |
| sharpe_5yr | DECIMAL(8,4) | 5-year Sharpe ratio |
| sharpe_10yr | DECIMAL(8,4) | 10-year Sharpe ratio |
| created_at | TIMESTAMP | Record creation time |

### Text-to-SQL Examples

**1. "Find funds with best risk-adjusted returns (highest 5-year Sharpe ratio)"**
```sql
SELECT s.scheme_name, s.amfi_sub, s.risk_level,
       sr.yrs5, sh.sharpe_5yr
FROM schemes s
JOIN scheme_returns sr ON s.id = sr.scheme_id
JOIN sharpe_ratios sh ON s.id = sh.scheme_id
WHERE sh.sharpe_5yr IS NOT NULL
ORDER BY sh.sharpe_5yr DESC
LIMIT 15;
```

**2. "Compare Sharpe ratios across different risk levels"**
```sql
SELECT s.risk_level,
       COUNT(*) as fund_count,
       ROUND(AVG(sh.sharpe_3yr), 3) as avg_sharpe_3yr,
       ROUND(AVG(sh.sharpe_5yr), 3) as avg_sharpe_5yr,
       ROUND(AVG(sr.yrs5), 2) as avg_return_5yr
FROM schemes s
JOIN sharpe_ratios sh ON s.id = sh.scheme_id
JOIN scheme_returns sr ON s.id = sr.scheme_id
WHERE sh.sharpe_5yr IS NOT NULL
GROUP BY s.risk_level
ORDER BY s.risk_level;
```

**3. "Find high-return funds with poor risk adjustment (low Sharpe ratio)"**
```sql
SELECT s.scheme_name, s.amfi_sub, sr.yrs5, sh.sharpe_5yr,
       (sr.yrs5 / NULLIF(sh.sharpe_5yr, 0)) as return_to_sharpe_ratio
FROM schemes s
JOIN scheme_returns sr ON s.id = sr.scheme_id
JOIN sharpe_ratios sh ON s.id = sh.scheme_id
WHERE sr.yrs5 > 20 AND sh.sharpe_5yr < 0.8
ORDER BY sr.yrs5 DESC;
```

**4. "Identify consistently good risk-adjusted performers across time periods"**
```sql
SELECT s.scheme_name, s.amfi_broad,
       sh.sharpe_3yr, sh.sharpe_5yr, sh.sharpe_10yr
FROM schemes s
JOIN sharpe_ratios sh ON s.id = sh.scheme_id
WHERE sh.sharpe_3yr > 0.8 
    AND sh.sharpe_5yr > 0.8 
    AND sh.sharpe_10yr > 0.5
ORDER BY (sh.sharpe_3yr + sh.sharpe_5yr + sh.sharpe_10yr) DESC;
```

**5. "Show Sharpe ratio distribution by fund category"**
```sql
SELECT s.amfi_broad,
       COUNT(*) as funds_with_sharpe,
       MIN(sh.sharpe_5yr) as min_sharpe,
       ROUND(AVG(sh.sharpe_5yr), 3) as avg_sharpe,
       MAX(sh.sharpe_5yr) as max_sharpe,
       ROUND(STDDEV(sh.sharpe_5yr), 3) as sharpe_volatility
FROM schemes s
JOIN sharpe_ratios sh ON s.id = sh.scheme_id
WHERE sh.sharpe_5yr IS NOT NULL
GROUP BY s.amfi_broad
ORDER BY avg_sharpe DESC;
```

---

## 4. BSE_DETAILS Table

**Purpose**: BSE trading information and transaction capabilities

| Column | Type | Description |
|--------|------|-------------|
| id | SERIAL (PK) | Auto-increment primary key |
| scheme_id | TEXT (FK) | References schemes.id |
| bse_code | TEXT | BSE trading code |
| sip_flag | BOOLEAN | SIP transactions allowed |
| stp_flag | BOOLEAN | STP (Systematic Transfer Plan) allowed |
| swp_flag | BOOLEAN | SWP (Systematic Withdrawal Plan) allowed |
| switch_flag | BOOLEAN | Fund switching allowed |
| lock_in_flag | BOOLEAN | Lock-in period applicable |
| lock_in_period_months | INTEGER | Lock-in duration in months |
| exit_load_flag | BOOLEAN | Exit load applicable |
| exit_load_message | TEXT | Detailed exit load conditions |
| created_at | TIMESTAMP | Record creation time |

### Text-to-SQL Examples

**1. "Find funds with no exit load for immediate liquidity"**
```sql
SELECT s.scheme_name, s.amfi_broad, b.bse_code, b.exit_load_message
FROM schemes s
JOIN bse_details b ON s.id = b.scheme_id
WHERE b.exit_load_flag = false
ORDER BY s.aum_in_lakhs DESC;
```

**2. "Show funds supporting all transaction types (SIP, STP, SWP, Switch)"**
```sql
SELECT s.scheme_name, s.amfi_sub, b.bse_code
FROM schemes s
JOIN bse_details b ON s.id = b.scheme_id
WHERE b.sip_flag = true 
    AND b.stp_flag = true 
    AND b.swp_flag = true 
    AND b.switch_flag = true
ORDER BY s.scheme_name;
```

**3. "List ELSS funds with their lock-in periods"**
```sql
SELECT s.scheme_name, b.lock_in_period_months, b.exit_load_message
FROM schemes s
JOIN bse_details b ON s.id = b.scheme_id
WHERE s.amfi_sub = 'ELSS' OR b.lock_in_flag = true
ORDER BY b.lock_in_period_months DESC NULLS LAST;
```

**4. "Find funds with complex exit load structures"**
```sql
SELECT s.scheme_name, s.amfi_sub, b.exit_load_message
FROM schemes s
JOIN bse_details b ON s.id = b.scheme_id
WHERE b.exit_load_flag = true 
    AND LENGTH(b.exit_load_message) > 100
ORDER BY LENGTH(b.exit_load_message) DESC;
```

**5. "Count transaction capabilities by fund category"**
```sql
SELECT s.amfi_broad,
       COUNT(*) as total_options,
       SUM(CASE WHEN b.sip_flag THEN 1 ELSE 0 END) as sip_enabled,
       SUM(CASE WHEN b.swp_flag THEN 1 ELSE 0 END) as swp_enabled,
       SUM(CASE WHEN b.switch_flag THEN 1 ELSE 0 END) as switch_enabled,
       SUM(CASE WHEN b.exit_load_flag THEN 1 ELSE 0 END) as with_exit_load
FROM schemes s
JOIN bse_details b ON s.id = b.scheme_id
GROUP BY s.amfi_broad
ORDER BY total_options DESC;
```

---

## 5. SIP_CONFIGURATIONS Table

**Purpose**: Systematic Investment Plan parameters and limits

| Column | Type | Description |
|--------|------|-------------|
| id | SERIAL (PK) | Auto-increment primary key |
| bse_detail_id | INTEGER (FK) | References bse_details.id |
| sip_type | TEXT | 'regular' or 'daily' SIP |
| min_amount | DECIMAL(15,2) | Minimum SIP amount |
| max_amount | DECIMAL(15,2) | Maximum SIP amount |
| amount_delta | DECIMAL(15,2) | Amount increment step |
| min_installments | INTEGER | Minimum number of installments |
| max_installments | INTEGER | Maximum number of installments |
| allowed_dates | JSONB | Array of allowed SIP dates (1-31) |
| created_at | TIMESTAMP | Record creation time |

### Text-to-SQL Examples

**1. "Find funds with very low minimum SIP amounts (under ₹500)"**
```sql
SELECT s.scheme_name, s.amfi_sub, sip.min_amount, sip.sip_type, b.bse_code
FROM schemes s
JOIN bse_details b ON s.id = b.scheme_id
JOIN sip_configurations sip ON b.id = sip.bse_detail_id
WHERE sip.min_amount <= 500
ORDER BY sip.min_amount, s.scheme_name;
```

**2. "Show daily SIP options with their minimum requirements"**
```sql
SELECT s.scheme_name, s.amfi_broad, sip.min_amount, sip.min_installments
FROM schemes s
JOIN bse_details b ON s.id = b.scheme_id
JOIN sip_configurations sip ON b.id = sip.bse_detail_id
WHERE sip.sip_type = 'daily'
ORDER BY sip.min_amount;
```

**3. "Find flexible SIP options with wide amount ranges"**
```sql
SELECT s.scheme_name, sip.min_amount, sip.max_amount,
       (sip.max_amount - sip.min_amount) as amount_range,
       sip.allowed_dates
FROM schemes s
JOIN bse_details b ON s.id = b.scheme_id
JOIN sip_configurations sip ON b.id = sip.bse_detail_id
WHERE sip.max_amount > sip.min_amount * 100
ORDER BY amount_range DESC;
```

**4. "Show SIP date flexibility by extracting allowed dates"**
```sql
SELECT s.scheme_name, sip.sip_type, sip.min_amount,
       jsonb_array_length(sip.allowed_dates) as date_options,
       sip.allowed_dates
FROM schemes s
JOIN bse_details b ON s.id = b.scheme_id
JOIN sip_configurations sip ON b.id = sip.bse_detail_id
WHERE sip.allowed_dates IS NOT NULL
ORDER BY date_options DESC;
```

**5. "Compare SIP parameters across fund categories"**
```sql
SELECT s.amfi_broad,
       COUNT(*) as sip_options,
       MIN(sip.min_amount) as lowest_min_sip,
       ROUND(AVG(sip.min_amount), 2) as avg_min_sip,
       MAX(sip.max_amount) as highest_max_sip
FROM schemes s
JOIN bse_details b ON s.id = b.scheme_id
JOIN sip_configurations sip ON b.id = sip.bse_detail_id
GROUP BY s.amfi_broad
ORDER BY avg_min_sip;
```

---

## 6. TRANSACTION_CONFIGURATIONS Table

**Purpose**: Purchase and redemption rules and limits

| Column | Type | Description |
|--------|------|-------------|
| id | SERIAL (PK) | Auto-increment primary key |
| bse_detail_id | INTEGER (FK) | References bse_details.id |
| transaction_type | TEXT | 'purchase' or 'redemption' |
| allowed | BOOLEAN | Transaction type allowed |
| min_amount | DECIMAL(15,2) | Minimum transaction amount |
| max_amount | DECIMAL(15,2) | Maximum transaction amount |
| amount_delta | DECIMAL(15,2) | Amount increment step |
| min_quantity | DECIMAL(15,6) | Minimum units for transaction |
| max_quantity | DECIMAL(15,6) | Maximum units for transaction |
| quantity_delta | DECIMAL(15,6) | Unit increment step |
| fresh_min | DECIMAL(15,2) | Minimum fresh investment |
| additional_min | DECIMAL(15,2) | Minimum additional investment |
| created_at | TIMESTAMP | Record creation time |

### Text-to-SQL Examples

**1. "Find funds with low minimum purchase amounts for new investors"**
```sql
SELECT s.scheme_name, s.amfi_sub, tc.fresh_min, tc.additional_min
FROM schemes s
JOIN bse_details b ON s.id = b.scheme_id
JOIN transaction_configurations tc ON b.id = tc.bse_detail_id
WHERE tc.transaction_type = 'purchase' 
    AND tc.allowed = true
    AND tc.fresh_min <= 1000
ORDER BY tc.fresh_min;
```

**2. "Show redemption flexibility (funds allowing partial redemptions)"**
```sql
SELECT s.scheme_name, s.amfi_broad, tc.min_amount as min_redemption,
       tc.min_quantity as min_units_redemption
FROM schemes s
JOIN bse_details b ON s.id = b.scheme_id
JOIN transaction_configurations tc ON b.id = tc.bse_detail_id
WHERE tc.transaction_type = 'redemption' 
    AND tc.allowed = true
ORDER BY tc.min_amount NULLS LAST;
```

**3. "Compare purchase vs redemption limits for the same fund"**
```sql
SELECT s.scheme_name,
       MAX(CASE WHEN tc.transaction_type = 'purchase' THEN tc.fresh_min END) as min_purchase,
       MAX(CASE WHEN tc.transaction_type = 'redemption' THEN tc.min_amount END) as min_redemption,
       MAX(CASE WHEN tc.transaction_type = 'purchase' THEN tc.allowed END) as purchase_allowed,
       MAX(CASE WHEN tc.transaction_type = 'redemption' THEN tc.allowed END) as redemption_allowed
FROM schemes s
JOIN bse_details b ON s.id = b.scheme_id
JOIN transaction_configurations tc ON b.id = tc.bse_detail_id
GROUP BY s.scheme_name, s.id
HAVING COUNT(DISTINCT tc.transaction_type) = 2
ORDER BY min_purchase;
```

**4. "Find funds with high minimum investment requirements (premium funds)"**
```sql
SELECT s.scheme_name, s.amfi_sub, s.aum_in_lakhs, tc.fresh_min
FROM schemes s
JOIN bse_details b ON s.id = b.scheme_id
JOIN transaction_configurations tc ON b.id = tc.bse_detail_id
WHERE tc.transaction_type = 'purchase' 
    AND tc.fresh_min > 100000
ORDER BY tc.fresh_min DESC;
```

**5. "Analyze transaction accessibility by fund category"**
```sql
SELECT s.amfi_broad,
       COUNT(*) as total_transaction_configs,
       SUM(CASE WHEN tc.transaction_type = 'purchase' AND tc.allowed THEN 1 ELSE 0 END) as purchase_enabled,
       SUM(CASE WHEN tc.transaction_type = 'redemption' AND tc.allowed THEN 1 ELSE 0 END) as redemption_enabled,
       ROUND(AVG(CASE WHEN tc.transaction_type = 'purchase' THEN tc.fresh_min END), 2) as avg_min_investment
FROM schemes s
JOIN bse_details b ON s.id = b.scheme_id
JOIN transaction_configurations tc ON b.id = tc.bse_detail_id
GROUP BY s.amfi_broad
ORDER BY avg_min_investment;
```

---

## Advanced Multi-Table Queries

### Portfolio Construction Query
```sql
-- Build a diversified portfolio with different risk levels and categories
SELECT 
    s.amfi_broad,
    s.scheme_name,
    s.risk_level,
    sr.yrs5 as five_year_return,
    sh.sharpe_5yr,
    sip.min_amount as min_sip,
    CASE WHEN b.exit_load_flag THEN 'Yes' ELSE 'No' END as exit_load
FROM schemes s
JOIN scheme_returns sr ON s.id = sr.scheme_id
LEFT JOIN sharpe_ratios sh ON s.id = sh.scheme_id
JOIN bse_details b ON s.id = b.scheme_id
JOIN sip_configurations sip ON b.id = sip.bse_detail_id
WHERE s.sip_allowed = true 
    AND sip.min_amount <= 2000
    AND sr.yrs5 > 12
    AND s.risk_level BETWEEN 2 AND 4
ORDER BY s.amfi_broad, sr.yrs5 DESC;
```

### Investment Platform Query
```sql
-- Complete fund information for investment platform display
SELECT 
    s.scheme_name,
    s.amfi_broad || ' - ' || s.amfi_sub as category,
    s.current_nav,
    s.aum_in_lakhs,
    s.risk_level,
    sr.yrs1, sr.yrs3, sr.yrs5,
    sh.sharpe_5yr,
    sip.min_amount as min_sip,
    tc.fresh_min as min_lumpsum,
    b.exit_load_message
FROM schemes s
LEFT JOIN scheme_returns sr ON s.id = sr.scheme_id
LEFT JOIN sharpe_ratios sh ON s.id = sh.scheme_id
LEFT JOIN bse_details b ON s.id = b.scheme_id
LEFT JOIN sip_configurations sip ON b.id = sip.bse_detail_id AND sip.sip_type = 'regular'
LEFT JOIN transaction_configurations tc ON b.id = tc.bse_detail_id AND tc.transaction_type = 'purchase'
WHERE s.purchase_allowed = true OR s.sip_allowed = true
ORDER BY s.aum_in_lakhs DESC;
```

---

## Database Maintenance

### Update Script
```bash
# Refresh data from MF APIs Club
python3 setup_mfapis_club_postgresql.py
```

### Backup Command
```bash
pg_dump mutual_fund > mutual_fund_backup_$(date +%Y%m%d).sql
```

### Performance Optimization
- All foreign keys have indexes
- Frequently queried columns are indexed
- JSONB columns support GIN indexes for array operations

---

## 7. HISTORICAL_NAV Table

**Purpose**: Complete historical Net Asset Value data for all mutual fund schemes

| Column | Type | Description |
|--------|------|-------------|
| id | SERIAL (PK) | Auto-increment primary key |
| scheme_id | TEXT (FK) | References schemes.id |
| scheme_code | TEXT | AMFI scheme code for reference |
| nav_date | DATE | Date of NAV record |
| nav_value | DECIMAL(12,6) | Net Asset Value on the date |
| data_source | TEXT | Data source ('mfapi') |
| created_at | TIMESTAMP | Record creation time |
| updated_at | TIMESTAMP | Last update time |

**Indexes**: Optimized for date-range queries and scheme lookups
- `idx_historical_nav_scheme_date` (scheme_id, nav_date DESC)
- `idx_historical_nav_date` (nav_date DESC)
- `idx_historical_nav_scheme_code` (scheme_code)

**Data Coverage**: 3,037,708 records spanning April 1, 2006 to September 10, 2025

### Text-to-SQL Examples

**1. "Calculate 1-year returns for all equity funds as of latest date"**
```sql
WITH latest_nav AS (
    SELECT h.scheme_id, h.nav_value as current_nav, h.nav_date as current_date
    FROM historical_nav h
    INNER JOIN (
        SELECT scheme_id, MAX(nav_date) as max_date
        FROM historical_nav
        GROUP BY scheme_id
    ) latest ON h.scheme_id = latest.scheme_id AND h.nav_date = latest.max_date
),
year_ago_nav AS (
    SELECT DISTINCT ON (h.scheme_id) 
        h.scheme_id, h.nav_value as year_ago_nav, h.nav_date as year_ago_date
    FROM historical_nav h
    INNER JOIN latest_nav l ON h.scheme_id = l.scheme_id
    WHERE h.nav_date <= l.current_date - INTERVAL '1 year'
    ORDER BY h.scheme_id, h.nav_date DESC
)
SELECT 
    s.scheme_name,
    s.amfi_sub,
    l.current_nav,
    y.year_ago_nav,
    ROUND(((l.current_nav - y.year_ago_nav) / y.year_ago_nav * 100), 2) as one_year_return_pct,
    l.current_date,
    y.year_ago_date
FROM schemes s
JOIN latest_nav l ON s.id = l.scheme_id
JOIN year_ago_nav y ON s.id = y.scheme_id
WHERE s.amfi_broad = 'Equity'
ORDER BY one_year_return_pct DESC
LIMIT 20;
```

**2. "Find the most volatile funds based on NAV standard deviation over last 2 years"**
```sql
SELECT 
    s.scheme_name,
    s.amfi_broad,
    s.amfi_sub,
    COUNT(h.nav_date) as data_points,
    ROUND(AVG(h.nav_value), 4) as avg_nav,
    ROUND(STDDEV(h.nav_value), 4) as nav_stddev,
    ROUND((STDDEV(h.nav_value) / AVG(h.nav_value) * 100), 2) as coefficient_of_variation
FROM schemes s
JOIN historical_nav h ON s.id = h.scheme_id
WHERE h.nav_date >= CURRENT_DATE - INTERVAL '2 years'
GROUP BY s.id, s.scheme_name, s.amfi_broad, s.amfi_sub
HAVING COUNT(h.nav_date) >= 400  -- Ensure sufficient data points
ORDER BY coefficient_of_variation DESC
LIMIT 15;
```

**3. "Show NAV growth trajectory for top 5 large cap funds over last 5 years"**
```sql
WITH top_large_cap AS (
    SELECT s.id, s.scheme_name, s.aum_in_lakhs
    FROM schemes s
    WHERE s.amfi_sub = 'Large Cap Fund'
    ORDER BY s.aum_in_lakhs DESC
    LIMIT 5
),
monthly_nav AS (
    SELECT 
        h.scheme_id,
        DATE_TRUNC('month', h.nav_date) as month_year,
        AVG(h.nav_value) as avg_monthly_nav,
        MIN(h.nav_value) as min_monthly_nav,
        MAX(h.nav_value) as max_monthly_nav
    FROM historical_nav h
    JOIN top_large_cap t ON h.scheme_id = t.id
    WHERE h.nav_date >= CURRENT_DATE - INTERVAL '5 years'
    GROUP BY h.scheme_id, DATE_TRUNC('month', h.nav_date)
)
SELECT 
    s.scheme_name,
    m.month_year,
    ROUND(m.avg_monthly_nav, 4) as avg_nav,
    ROUND(m.min_monthly_nav, 4) as min_nav,
    ROUND(m.max_monthly_nav, 4) as max_nav,
    ROUND(((m.max_monthly_nav - m.min_monthly_nav) / m.avg_monthly_nav * 100), 2) as monthly_volatility_pct
FROM monthly_nav m
JOIN schemes s ON m.scheme_id = s.id
ORDER BY s.scheme_name, m.month_year;
```

**4. "Identify funds that have consistently grown NAV (no negative months) in last 3 years"**
```sql
WITH monthly_returns AS (
    SELECT 
        h.scheme_id,
        DATE_TRUNC('month', h.nav_date) as month_year,
        FIRST_VALUE(h.nav_value) OVER (
            PARTITION BY h.scheme_id, DATE_TRUNC('month', h.nav_date) 
            ORDER BY h.nav_date
        ) as month_start_nav,
        LAST_VALUE(h.nav_value) OVER (
            PARTITION BY h.scheme_id, DATE_TRUNC('month', h.nav_date) 
            ORDER BY h.nav_date 
            RANGE BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING
        ) as month_end_nav
    FROM historical_nav h
    WHERE h.nav_date >= CURRENT_DATE - INTERVAL '3 years'
),
monthly_performance AS (
    SELECT DISTINCT
        scheme_id,
        month_year,
        ((month_end_nav - month_start_nav) / month_start_nav * 100) as monthly_return_pct
    FROM monthly_returns
),
consistent_performers AS (
    SELECT 
        scheme_id,
        COUNT(*) as total_months,
        SUM(CASE WHEN monthly_return_pct >= 0 THEN 1 ELSE 0 END) as positive_months,
        ROUND(AVG(monthly_return_pct), 2) as avg_monthly_return
    FROM monthly_performance
    GROUP BY scheme_id
    HAVING COUNT(*) >= 30  -- At least 30 months of data
        AND SUM(CASE WHEN monthly_return_pct >= 0 THEN 1 ELSE 0 END) = COUNT(*)  -- All positive
)
SELECT 
    s.scheme_name,
    s.amfi_broad,
    s.amfi_sub,
    cp.total_months,
    cp.avg_monthly_return,
    ROUND((POWER(1 + cp.avg_monthly_return/100, 12) - 1) * 100, 2) as annualized_return_pct
FROM consistent_performers cp
JOIN schemes s ON cp.scheme_id = s.id
ORDER BY cp.avg_monthly_return DESC;
```

**5. "Compare NAV performance during market crash periods (identify resilient funds)"**
```sql
-- Define market crash periods (major corrections)
WITH crash_periods AS (
    SELECT '2020-02-01'::date as start_date, '2020-04-30'::date as end_date, 'COVID-19 Crash' as period_name
    UNION ALL
    SELECT '2018-01-01'::date, '2018-12-31'::date, '2018 Market Correction'
    UNION ALL
    SELECT '2015-08-01'::date, '2016-02-29'::date, '2015-16 Slowdown'
),
crash_performance AS (
    SELECT 
        h.scheme_id,
        cp.period_name,
        FIRST_VALUE(h.nav_value) OVER (
            PARTITION BY h.scheme_id, cp.period_name 
            ORDER BY h.nav_date
        ) as start_nav,
        LAST_VALUE(h.nav_value) OVER (
            PARTITION BY h.scheme_id, cp.period_name 
            ORDER BY h.nav_date 
            RANGE BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING
        ) as end_nav
    FROM historical_nav h
    CROSS JOIN crash_periods cp
    WHERE h.nav_date BETWEEN cp.start_date AND cp.end_date
),
crash_returns AS (
    SELECT DISTINCT
        scheme_id,
        period_name,
        ((end_nav - start_nav) / start_nav * 100) as crash_return_pct
    FROM crash_performance
),
resilient_funds AS (
    SELECT 
        scheme_id,
        COUNT(*) as crash_periods_covered,
        ROUND(AVG(crash_return_pct), 2) as avg_crash_return,
        MIN(crash_return_pct) as worst_crash_return
    FROM crash_returns
    GROUP BY scheme_id
    HAVING COUNT(*) >= 2  -- Covered at least 2 crash periods
        AND AVG(crash_return_pct) > -15  -- Average loss less than 15%
)
SELECT 
    s.scheme_name,
    s.amfi_broad,
    s.amfi_sub,
    rf.crash_periods_covered,
    rf.avg_crash_return,
    rf.worst_crash_return,
    s.aum_in_lakhs
FROM resilient_funds rf
JOIN schemes s ON rf.scheme_id = s.id
ORDER BY rf.avg_crash_return DESC;
```

**6. "Calculate rolling 252-day (1-year) Sharpe ratio for funds using daily NAV data"**
```sql
WITH daily_returns AS (
    SELECT 
        h.scheme_id,
        h.nav_date,
        h.nav_value,
        LAG(h.nav_value) OVER (PARTITION BY h.scheme_id ORDER BY h.nav_date) as prev_nav,
        ((h.nav_value - LAG(h.nav_value) OVER (PARTITION BY h.scheme_id ORDER BY h.nav_date)) 
         / LAG(h.nav_value) OVER (PARTITION BY h.scheme_id ORDER BY h.nav_date) * 100) as daily_return_pct
    FROM historical_nav h
    WHERE h.nav_date >= CURRENT_DATE - INTERVAL '2 years'
),
rolling_metrics AS (
    SELECT 
        scheme_id,
        nav_date,
        AVG(daily_return_pct) OVER (
            PARTITION BY scheme_id 
            ORDER BY nav_date 
            ROWS BETWEEN 251 PRECEDING AND CURRENT ROW
        ) as rolling_avg_return,
        STDDEV(daily_return_pct) OVER (
            PARTITION BY scheme_id 
            ORDER BY nav_date 
            ROWS BETWEEN 251 PRECEDING AND CURRENT ROW
        ) as rolling_volatility,
        COUNT(*) OVER (
            PARTITION BY scheme_id 
            ORDER BY nav_date 
            ROWS BETWEEN 251 PRECEDING AND CURRENT ROW
        ) as data_points
    FROM daily_returns
    WHERE daily_return_pct IS NOT NULL
),
latest_sharpe AS (
    SELECT DISTINCT ON (scheme_id)
        scheme_id,
        nav_date,
        rolling_avg_return * 252 as annualized_return,  -- Assuming 252 trading days
        rolling_volatility * SQRT(252) as annualized_volatility,
        CASE 
            WHEN rolling_volatility > 0 THEN 
                (rolling_avg_return * 252 - 6) / (rolling_volatility * SQRT(252))  -- Assuming 6% risk-free rate
            ELSE NULL 
        END as rolling_sharpe_ratio
    FROM rolling_metrics
    WHERE data_points = 252  -- Full year of data
    ORDER BY scheme_id, nav_date DESC
)
SELECT 
    s.scheme_name,
    s.amfi_broad,
    s.amfi_sub,
    ls.nav_date as calculation_date,
    ROUND(ls.annualized_return, 2) as annualized_return_pct,
    ROUND(ls.annualized_volatility, 2) as annualized_volatility_pct,
    ROUND(ls.rolling_sharpe_ratio, 3) as rolling_sharpe_ratio
FROM latest_sharpe ls
JOIN schemes s ON ls.scheme_id = s.id
WHERE ls.rolling_sharpe_ratio IS NOT NULL
ORDER BY ls.rolling_sharpe_ratio DESC
LIMIT 25;
```

---

## Advanced Time-Series Analysis Queries

### Portfolio Performance Tracking
```sql
-- Track a hypothetical SIP investment over time
WITH sip_simulation AS (
    SELECT 
        h.scheme_id,
        h.nav_date,
        h.nav_value,
        1000 as monthly_sip_amount,  -- ₹1000 monthly SIP
        CASE 
            WHEN EXTRACT(day FROM h.nav_date) = 1 THEN 1000 / h.nav_value 
            ELSE 0 
        END as units_purchased
    FROM historical_nav h
    WHERE h.nav_date >= '2020-01-01'
        AND EXTRACT(day FROM h.nav_date) = 1  -- First day of month
),
cumulative_investment AS (
    SELECT 
        scheme_id,
        nav_date,
        nav_value,
        SUM(monthly_sip_amount) OVER (PARTITION BY scheme_id ORDER BY nav_date) as total_invested,
        SUM(units_purchased) OVER (PARTITION BY scheme_id ORDER BY nav_date) as total_units
    FROM sip_simulation
)
SELECT 
    s.scheme_name,
    ci.nav_date,
    ci.total_invested,
    ROUND(ci.total_units, 4) as total_units,
    ROUND(ci.total_units * ci.nav_value, 2) as current_value,
    ROUND(((ci.total_units * ci.nav_value - ci.total_invested) / ci.total_invested * 100), 2) as returns_pct
FROM cumulative_investment ci
JOIN schemes s ON ci.scheme_id = s.id
WHERE s.amfi_sub = 'Large Cap Fund'
ORDER BY s.scheme_name, ci.nav_date;
```

### Market Correlation Analysis
```sql
-- Calculate correlation between funds and market index
WITH nifty_proxy AS (
    SELECT nav_date, nav_value as nifty_nav
    FROM historical_nav h
    JOIN schemes s ON h.scheme_id = s.id
    WHERE s.scheme_name ILIKE '%nifty 50%index%'
    LIMIT 1
),
fund_returns AS (
    SELECT 
        h.scheme_id,
        h.nav_date,
        ((h.nav_value - LAG(h.nav_value) OVER (PARTITION BY h.scheme_id ORDER BY h.nav_date)) 
         / LAG(h.nav_value) OVER (PARTITION BY h.scheme_id ORDER BY h.nav_date)) as fund_return,
        ((n.nifty_nav - LAG(n.nifty_nav) OVER (ORDER BY h.nav_date)) 
         / LAG(n.nifty_nav) OVER (ORDER BY h.nav_date)) as nifty_return
    FROM historical_nav h
    JOIN nifty_proxy n ON h.nav_date = n.nav_date
    WHERE h.nav_date >= CURRENT_DATE - INTERVAL '1 year'
)
SELECT 
    s.scheme_name,
    s.amfi_sub,
    COUNT(*) as data_points,
    ROUND(CORR(fr.fund_return, fr.nifty_return)::numeric, 3) as correlation_with_nifty,
    ROUND(AVG(fr.fund_return * 100), 3) as avg_daily_return_pct,
    ROUND(STDDEV(fr.fund_return * 100), 3) as daily_volatility_pct
FROM fund_returns fr
JOIN schemes s ON fr.scheme_id = s.id
WHERE fr.fund_return IS NOT NULL AND fr.nifty_return IS NOT NULL
GROUP BY s.id, s.scheme_name, s.amfi_sub
HAVING COUNT(*) >= 200  -- Sufficient data points
ORDER BY correlation_with_nifty DESC;
```

---

*Last Updated: September 11, 2025*
*Total Records: 3,052,270 across 7 tables (including 3,037,708 historical NAV records)*
*Data Sources: MF APIs Club (https://app.mfapis.club) + MFApi.in (https://api.mfapi.in)*
