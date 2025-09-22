# Mutual Fund Database Schema Documentation

## Overview

The `mutual_fund` PostgreSQL database contains comprehensive mutual fund data from MFAPIs Club with 6 interconnected tables storing 6.3M+ records across 1,487 mutual fund schemes.

### Database Statistics (Updated: September 2025)
- **Total Schemes**: 1,487 (100% coverage)
- **Historical NAV Records**: 3,147,643 (19+ years: 2006-2025)
- **Historical Returns Records**: 1,487 (one per scheme with latest metrics)
- **Historical Risk Records**: 1,308 (comprehensive risk metrics)
- **Fund Rankings Records**: 1,484 (sophisticated ranking algorithm)
- **Current Holdings Records**: 51,950 (comprehensive portfolio data)
- **BSE Trading Details**: 1,487 (100% coverage)
- **Total Database Size**: ~3.2 GB
- **Total Records Processed**: 6,352,051

### Data Sources
- **Primary API**: https://app.mfapis.club/api/v1 (MFAPIs Club)
- **Backup NAV**: https://api.mfapi.in (fallback)
- **Update Frequency**: Real-time via modular ETL pipeline
- **Coverage**: All 1,487 AMFI registered mutual funds
- **Historical Depth**: 19+ years (April 2006 - September 2025)

---

## Table Relationships

```
schemes (1:M) → historical_nav
schemes (1:1) → historical_returns  
schemes (1:M) → historical_risk
schemes (1:M) → current_holdings
schemes (1:1) → bse_details
schemes (1:1) → fund_rankings
```

### Foreign Key Constraints
- All child tables reference `schemes.id` with CASCADE options
- Unique constraints prevent duplicate records
- Optimized indexes for performance queries

---

## 1. SCHEMES Table

**Purpose**: Core mutual fund information and metadata
**Records**: 1,487 schemes (100% AMFI coverage)
**Table Size**: 1,048 kB

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| id | TEXT (PK) | NO | - | Unique scheme identifier from MFAPIs Club |
| scheme_code | TEXT | YES | - | AMFI scheme code |
| scheme_name | TEXT | NO | - | Full scheme name |
| aum_in_lakhs | NUMERIC | YES | - | Assets Under Management in lakhs |
| amfi_broad | TEXT | YES | - | Broad category (Equity, Debt, Hybrid, Other, Solution Oriented) |
| amfi_sub | TEXT | YES | - | Sub-category (Large Cap Fund, Liquid Fund, etc.) |
| isin | TEXT | YES | - | International Securities Identification Number |
| scheme_type | TEXT | YES | - | Scheme type classification |
| legend | TEXT | YES | - | Scheme legend/status |
| risk_level | TEXT | YES | - | Risk level description |
| horizon | TEXT | YES | - | Investment horizon recommendation |
| load_months | INTEGER | YES | - | Load period in months |
| is_recommended | BOOLEAN | YES | false | Whether scheme is recommended |
| amc_code | TEXT | YES | - | Asset Management Company code |
| div_reinvest | TEXT | YES | - | Dividend reinvestment option |
| purchase_allowed | BOOLEAN | YES | true | Lump sum purchase allowed |

**Indexes**:
- `schemes_pkey` (PRIMARY KEY on id)
- `idx_schemes_amfi_broad` (amfi_broad)
- `idx_schemes_scheme_code` (scheme_code)

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

## 2. HISTORICAL_NAV Table

**Purpose**: Complete historical Net Asset Value data for all mutual fund schemes
**Records**: 3,147,643 records (19+ years of data)
**Table Size**: 1,064 MB
**Date Range**: April 1, 2006 to September 10, 2025

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| id | INTEGER (PK) | NO | nextval() | Auto-increment primary key |
| scheme_id | TEXT (FK) | NO | - | References schemes.id |
| scheme_code | TEXT | NO | - | AMFI scheme code for reference |
| nav_date | DATE | NO | - | Date of NAV record |
| nav_value | NUMERIC | NO | - | Net Asset Value on the date |
| data_source | TEXT | NO | 'mfapis_club' | Data source identifier |
| created_at | TIMESTAMP | YES | CURRENT_TIMESTAMP | Record creation time |

**Constraints**:
- `historical_nav_pkey` (PRIMARY KEY on id)
- `historical_nav_scheme_id_nav_date_key` (UNIQUE on scheme_id, nav_date)
- `historical_nav_scheme_id_fkey` (FOREIGN KEY to schemes.id)

**Indexes**: Optimized for date-range queries and scheme lookups
- `idx_historical_nav_scheme_date` (scheme_id, nav_date DESC)
- `idx_historical_nav_date` (nav_date DESC)

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

## 3. HISTORICAL_RETURNS Table

**Purpose**: Latest NAV metrics and comprehensive returns analysis for all mutual fund schemes
**Records**: 1,487 records (one per scheme with latest metrics)
**Table Size**: 904 kB
**Coverage**: 100% of schemes with latest returns data

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| id | INTEGER (PK) | NO | nextval() | Auto-increment primary key |
| scheme_id | TEXT (FK) | NO | - | References schemes.id |
| scheme_code | TEXT | NO | - | AMFI scheme code for reference |
| scheme_name | TEXT | NO | - | Full scheme name |
| latest_nav_date | DATE | NO | - | Latest NAV date |
| latest_nav_value | NUMERIC | NO | - | Latest NAV value |
| return_1d | NUMERIC | YES | - | 1-day point-to-point return |
| return_1w | NUMERIC | YES | - | 1-week point-to-point return |
| return_1m | NUMERIC | YES | - | 1-month point-to-point return |
| return_3m | NUMERIC | YES | - | 3-month point-to-point return |
| return_6m | NUMERIC | YES | - | 6-month point-to-point return |
| return_1y | NUMERIC | YES | - | 1-year point-to-point return |
| return_3y | NUMERIC | YES | - | 3-year point-to-point return |
| return_5y | NUMERIC | YES | - | 5-year point-to-point return |
| return_7y | NUMERIC | YES | - | 7-year point-to-point return |
| return_10y | NUMERIC | YES | - | 10-year point-to-point return |
| annualized_1y | NUMERIC | YES | - | 1-year CAGR (annualized return) |
| annualized_3y | NUMERIC | YES | - | 3-year CAGR (annualized return) |
| annualized_5y | NUMERIC | YES | - | 5-year CAGR (annualized return) |
| annualized_7y | NUMERIC | YES | - | 7-year CAGR (annualized return) |
| annualized_10y | NUMERIC | YES | - | 10-year CAGR (annualized return) |
| rolling_return_1y | NUMERIC | YES | - | 1-year rolling return as of latest date |
| rolling_return_3y | NUMERIC | YES | - | 3-year rolling return as of latest date |
| rolling_return_5y | NUMERIC | YES | - | 5-year rolling return as of latest date |
| data_source | TEXT | YES | 'mfapis_club' | Data source identifier |
| created_at | TIMESTAMP | YES | CURRENT_TIMESTAMP | Record creation time |
| updated_at | TIMESTAMP | YES | CURRENT_TIMESTAMP | Last update time |

**Constraints**:
- `historical_returns_pkey` (PRIMARY KEY on id)
- `historical_returns_scheme_id_key` (UNIQUE on scheme_id)
- `historical_returns_scheme_id_fkey` (FOREIGN KEY to schemes.id)

**Indexes**: Optimized for performance analysis and latest metrics queries
- `idx_historical_returns_scheme_id` (scheme_id)
- `idx_historical_returns_latest_nav_date` (latest_nav_date DESC)

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

## 4. FUND_RANKINGS Table

**Purpose**: Sophisticated fund ranking system using thematic factor grouping with three-pillar approach
**Records**: 1,484 records (99.8% coverage - excludes 3 funds with AUM = 0)
**Table Size**: 904 kB
**Ranking Range**: 1 to 1,473 (overall ranking across all categories)

**Algorithm Overview**:
- **Pillar 1**: Risk-Adjusted Performance & Consistency (45% weight)
- **Pillar 2**: Downside Protection & Risk Management (35% weight)  
- **Pillar 3**: Cost Efficiency & Fund Health (20% weight)
- **Normalization**: Percentile ranking within AMFI categories (0-100 scale)
- **Final Score**: Weighted composite score with transparent pillar breakdown

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| id | INTEGER (PK) | NO | nextval() | Auto-increment primary key |
| scheme_id | TEXT (FK) | NO | - | References schemes.id |
| scheme_code | TEXT | NO | - | AMFI scheme code for reference |
| scheme_name | TEXT | NO | - | Full scheme name |
| amfi_broad | TEXT | NO | - | AMFI broad category (Equity, Debt, Hybrid, Other, Solution Oriented) |
| amfi_sub | TEXT | YES | - | AMFI sub-category (Large Cap Fund, Liquid Fund, etc.) |
| aum_cr | NUMERIC | YES | - | Assets Under Management in crores |
| nav | NUMERIC | YES | - | Latest NAV value |
| nav_date | DATE | YES | - | Latest NAV date |
| **composite_score** | **NUMERIC** | **YES** | **-** | **Final composite score (0-100) - primary ranking metric** |
| **overall_rank** | **INTEGER** | **YES** | **-** | **Overall ranking (1 to 1,473) across all funds** |
| **category_rank** | **INTEGER** | **YES** | **-** | **Ranking within AMFI broad category** |
| **pillar_1_score** | **NUMERIC** | **YES** | **-** | **Risk-Adjusted Performance pillar score (0-100)** |
| **pillar_2_score** | **NUMERIC** | **YES** | **-** | **Downside Protection pillar score (0-100)** |
| **pillar_3_score** | **NUMERIC** | **YES** | **-** | **Cost Efficiency pillar score (0-100)** |
| sharpe_ratio_3y | NUMERIC | YES | - | 3-year Sharpe ratio (reward per unit risk) |
| sortino_ratio_3y | NUMERIC | YES | - | 3-year Sortino ratio (downside deviation focus) |
| jensen_alpha_3y | NUMERIC | YES | - | 3-year Jensen's Alpha (excess return over benchmark) |
| avg_3y_rolling_return | NUMERIC | YES | - | Average 3-year rolling return |
| avg_5y_rolling_return | NUMERIC | YES | - | Average 5-year rolling return |
| maximum_drawdown_5y | NUMERIC | YES | - | Maximum drawdown over 5 years (risk measure) |
| annualized_volatility_3y | NUMERIC | YES | - | 3-year annualized volatility (risk measure) |
| annualized_volatility_5y | NUMERIC | YES | - | 5-year annualized volatility (risk measure) |
| down_capture_ratio_3y | NUMERIC | YES | - | 3-year down-capture ratio (downside protection) |
| var_95_1y | NUMERIC | YES | - | 1-year 95% Value at Risk |
| beta_3y | NUMERIC | YES | - | 3-year beta (market correlation) |
| fund_size_aum | NUMERIC | YES | - | Fund size in crores (for cost efficiency pillar) |
| annualized_return_3y | NUMERIC | YES | - | 3-year CAGR |
| annualized_return_5y | NUMERIC | YES | - | 5-year CAGR |
| point_to_point_return_1y | NUMERIC | YES | - | 1-year total return |
| point_to_point_return_3y | NUMERIC | YES | - | 3-year total return |
| point_to_point_return_5y | NUMERIC | YES | - | 5-year total return |
| calculation_date | DATE | YES | CURRENT_DATE | Date of ranking calculation |
| created_at | TIMESTAMP | YES | CURRENT_TIMESTAMP | Record creation time |
| updated_at | TIMESTAMP | YES | CURRENT_TIMESTAMP | Last update time |

**Constraints**:
- `fund_rankings_pkey` (PRIMARY KEY on id)
- `fund_rankings_scheme_id_calculation_date_key` (UNIQUE on scheme_id, calculation_date)
- `fund_rankings_scheme_id_fkey` (FOREIGN KEY to schemes.id)

**Indexes**: Optimized for ranking queries and performance analysis
- `idx_fund_rankings_overall_rank` (overall_rank) - Primary ranking index
- `idx_fund_rankings_composite_score` (composite_score DESC) - Score-based queries
- `idx_fund_rankings_category_rank` (amfi_broad, category_rank) - Category rankings
- `idx_fund_rankings_amfi_broad` (amfi_broad) - Category filtering
- `idx_fund_rankings_amfi_sub` (amfi_sub) - Sub-category filtering

### Ranking Methodology

**Three-Pillar Thematic Approach**:

1. **Pillar 1: Risk-Adjusted Performance & Consistency (45%)**
   - Sharpe Ratio (15%): Reward per unit of risk
   - Sortino Ratio (10%): Focus on downside deviation
   - Jensen's Alpha (7.5%): Manager skill assessment
   - Average 3Y Rolling Return (10%): Performance consistency
   - Average 5Y Rolling Return (7.5%): Long-term consistency

2. **Pillar 2: Downside Protection & Risk Management (35%)**
   - Maximum Drawdown 5Y (10.5%): Capital preservation
   - Annualized Volatility 3Y/5Y (7% each): Risk measurement
   - Down-capture Ratio (7%): Downside resilience
   - VaR 95% (5.25%): Tail risk assessment
   - Beta (5.25%): Market correlation

3. **Pillar 3: Cost Efficiency & Fund Health (20%)**
   - Fund Size/AUM (20%): Operational efficiency and stability

**Normalization Process**:
- Percentile ranking within AMFI broad categories (0-100 scale)
- "Lower is better" metrics inverted (volatility, drawdown, etc.)
- Robust to outliers, intuitive scoring system

### Text-to-SQL Examples

**1. "Show top 10 overall fund rankings across all categories"**
```sql
SELECT overall_rank, scheme_name, amfi_broad, composite_score,
       pillar_1_score, pillar_2_score, pillar_3_score
FROM fund_rankings 
ORDER BY overall_rank 
LIMIT 10;
```

**2. "Find best performing equity funds with detailed pillar breakdown"**
```sql
SELECT scheme_name, overall_rank, composite_score,
       pillar_1_score as performance_score,
       pillar_2_score as risk_mgmt_score,
       pillar_3_score as efficiency_score,
       annualized_return_3y, maximum_drawdown_5y
FROM fund_rankings 
WHERE amfi_broad = 'Equity'
ORDER BY overall_rank 
LIMIT 5;
```

**3. "Compare category leaders - top fund from each AMFI category"**
```sql
SELECT DISTINCT ON (amfi_broad) 
       amfi_broad, scheme_name, overall_rank, composite_score
FROM fund_rankings 
ORDER BY amfi_broad, overall_rank;
```

**4. "Find funds with excellent risk management (high Pillar 2 scores)"**
```sql
SELECT scheme_name, amfi_broad, overall_rank, pillar_2_score,
       maximum_drawdown_5y, annualized_volatility_3y
FROM fund_rankings 
WHERE pillar_2_score > 80
ORDER BY pillar_2_score DESC;
```

**5. "Analyze ranking distribution by category"**
```sql
SELECT amfi_broad,
       COUNT(*) as total_funds,
       ROUND(AVG(composite_score), 2) as avg_score,
       MIN(overall_rank) as best_rank,
       MAX(overall_rank) as worst_rank
FROM fund_rankings 
GROUP BY amfi_broad
ORDER BY avg_score DESC;
```

**6. "Portfolio construction: Find balanced funds across risk-return spectrum"**
```sql
SELECT scheme_name, amfi_broad, overall_rank, composite_score,
       annualized_return_3y, maximum_drawdown_5y, aum_cr
FROM fund_rankings 
WHERE pillar_1_score > 70  -- Good performance
  AND pillar_2_score > 60  -- Reasonable risk management
  AND aum_cr > 1000        -- Sufficient size
ORDER BY composite_score DESC;
```

---

## 5. HISTORICAL_RISK Table

**Purpose**: Comprehensive risk metrics and volatility analysis for mutual fund schemes
**Records**: 1,308 records (88% coverage for 1Y+ periods)
**Table Size**: 1,112 kB
**Risk Coverage by Period**:
- 1W-1Y: 1,308/1,487 schemes (88.0%)
- 3Y: 982/1,487 schemes (66.0%)
- 5Y: 785/1,487 schemes (52.8%)

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| id | INTEGER (PK) | NO | nextval() | Auto-increment primary key |
| scheme_id | TEXT (FK) | NO | - | References schemes.id |
| scheme_code | TEXT | NO | - | AMFI scheme code for reference |
| risk_date | DATE | NO | - | Date of risk calculation |
| volatility_1w | NUMERIC | YES | - | 1-week annualized volatility |
| volatility_1m | NUMERIC | YES | - | 1-month annualized volatility |
| volatility_3m | NUMERIC | YES | - | 3-month annualized volatility |
| volatility_6m | NUMERIC | YES | - | 6-month annualized volatility |
| volatility_1y | NUMERIC | YES | - | 1-year annualized volatility |
| volatility_3y | NUMERIC | YES | - | 3-year annualized volatility |
| volatility_5y | NUMERIC | YES | - | 5-year annualized volatility |
| sharpe_ratio_1w | NUMERIC | YES | - | 1-week Sharpe ratio |
| sharpe_ratio_1m | NUMERIC | YES | - | 1-month Sharpe ratio |
| sharpe_ratio_3m | NUMERIC | YES | - | 3-month Sharpe ratio |
| sharpe_ratio_6m | NUMERIC | YES | - | 6-month Sharpe ratio |
| sharpe_ratio_1y | NUMERIC | YES | - | 1-year Sharpe ratio |
| sharpe_ratio_3y | NUMERIC | YES | - | 3-year Sharpe ratio |
| sharpe_ratio_5y | NUMERIC | YES | - | 5-year Sharpe ratio |
| sortino_ratio_1w | NUMERIC | YES | - | 1-week Sortino ratio |
| sortino_ratio_1m | NUMERIC | YES | - | 1-month Sortino ratio |
| sortino_ratio_3m | NUMERIC | YES | - | 3-month Sortino ratio |
| sortino_ratio_6m | NUMERIC | YES | - | 6-month Sortino ratio |
| sortino_ratio_1y | NUMERIC | YES | - | 1-year Sortino ratio |
| sortino_ratio_3y | NUMERIC | YES | - | 3-year Sortino ratio |
| sortino_ratio_5y | NUMERIC | YES | - | 5-year Sortino ratio |
| beta_1w | NUMERIC | YES | - | 1-week beta (market correlation) |
| beta_1m | NUMERIC | YES | - | 1-month beta |
| beta_3m | NUMERIC | YES | - | 3-month beta |
| beta_6m | NUMERIC | YES | - | 6-month beta |
| beta_1y | NUMERIC | YES | - | 1-year beta |
| beta_3y | NUMERIC | YES | - | 3-year beta |
| beta_5y | NUMERIC | YES | - | 5-year beta |
| alpha_1w | NUMERIC | YES | - | 1-week alpha (excess return) |
| alpha_1m | NUMERIC | YES | - | 1-month alpha |
| alpha_3m | NUMERIC | YES | - | 3-month alpha |
| alpha_6m | NUMERIC | YES | - | 6-month alpha |
| alpha_1y | NUMERIC | YES | - | 1-year alpha |
| alpha_3y | NUMERIC | YES | - | 3-year alpha |
| alpha_5y | NUMERIC | YES | - | 5-year alpha |
| maximum_drawdown_1w | NUMERIC | YES | - | 1-week maximum drawdown |
| maximum_drawdown_1m | NUMERIC | YES | - | 1-month maximum drawdown |
| maximum_drawdown_3m | NUMERIC | YES | - | 3-month maximum drawdown |
| maximum_drawdown_6m | NUMERIC | YES | - | 6-month maximum drawdown |
| maximum_drawdown_1y | NUMERIC | YES | - | 1-year maximum drawdown |
| maximum_drawdown_3y | NUMERIC | YES | - | 3-year maximum drawdown |
| maximum_drawdown_5y | NUMERIC | YES | - | 5-year maximum drawdown |
| var_95_1y | NUMERIC | YES | - | 1-year 95% Value at Risk |
| up_capture_ratio_3y | NUMERIC | YES | - | 3-year up-capture ratio vs benchmark |
| down_capture_ratio_3y | NUMERIC | YES | - | 3-year down-capture ratio vs benchmark |
| created_at | TIMESTAMP | YES | CURRENT_TIMESTAMP | Record creation time |

**Constraints**:
- `historical_risk_pkey` (PRIMARY KEY on id)
- `historical_risk_scheme_id_unique` (UNIQUE on scheme_id)
- `historical_risk_scheme_id_fkey` (FOREIGN KEY to schemes.id)

**Indexes**:
- `idx_historical_risk_scheme_date` (scheme_id, risk_date DESC)

**Note**: 1D risk metrics are mathematically undefined (standard deviation of single value) and correctly excluded from calculations.

---

## 6. CURRENT_HOLDINGS Table

**Purpose**: Current portfolio holdings and asset allocation for mutual fund schemes
**Records**: 51,950 records (comprehensive portfolio compositions)
**Table Size**: 744 kB

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| id | INTEGER (PK) | NO | nextval() | Auto-increment primary key |
| scheme_id | TEXT (FK) | NO | - | References schemes.id |
| scheme_code | TEXT | NO | - | AMFI scheme code for reference |
| company_name | TEXT | NO | - | Name of the holding company/security |
| percentage_holding | NUMERIC | NO | - | Percentage of portfolio allocated to this holding |
| market_value | NUMERIC | YES | - | Market value of the holding |
| holding_date | DATE | NO | - | Date of the holdings data |
| investment_type | TEXT | YES | - | Type of investment (equity, debt, etc.) |
| sector | TEXT | YES | - | Sector classification of the holding |
| created_at | TIMESTAMP | YES | CURRENT_TIMESTAMP | Record creation time |

**Constraints**:
- `current_holdings_pkey` (PRIMARY KEY on id)
- `current_holdings_scheme_id_company_name_holding_date_key` (UNIQUE on scheme_id, company_name, holding_date)
- `current_holdings_scheme_id_fkey` (FOREIGN KEY to schemes.id)

**Indexes**:
- `idx_current_holdings_scheme_date` (scheme_id, holding_date DESC)
- `idx_current_holdings_company` (company_name)

---

## 7. BSE_DETAILS Table

**Purpose**: BSE trading information and transaction capabilities
**Records**: 1,487 records (100% coverage)
**Table Size**: 1,048 kB

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| id | INTEGER (PK) | NO | nextval() | Auto-increment primary key |
| scheme_id | TEXT (FK) | NO | - | References schemes.id |
| scheme_code | TEXT | NO | - | AMFI scheme code |
| bse_code | TEXT | YES | - | BSE trading code |
| bse_scheme_code | TEXT | YES | - | BSE scheme code |
| minimum_amount | NUMERIC | YES | - | Minimum investment amount |
| maximum_amount | NUMERIC | YES | - | Maximum investment amount |
| multiplier | NUMERIC | YES | 1 | Investment amount multiplier |
| purchase_allowed | BOOLEAN | YES | false | Purchase transactions allowed |
| redemption_allowed | BOOLEAN | YES | false | Redemption transactions allowed |
| sip_allowed | BOOLEAN | YES | false | SIP transactions allowed |
| stp_allowed | BOOLEAN | YES | false | STP (Systematic Transfer Plan) allowed |
| swp_allowed | BOOLEAN | YES | false | SWP (Systematic Withdrawal Plan) allowed |
| switch_allowed | BOOLEAN | YES | false | Fund switching allowed |
| exit_load | TEXT | YES | - | Exit load description |
| exit_load_days | INTEGER | YES | - | Exit load applicable days |
| lock_in_period | INTEGER | YES | - | Lock-in period in days |
| data_source | TEXT | YES | 'mfapis_club' | Data source identifier |
| created_at | TIMESTAMP | YES | CURRENT_TIMESTAMP | Record creation time |
| updated_at | TIMESTAMP | YES | CURRENT_TIMESTAMP | Last update time |

**Constraints**:
- `bse_details_pkey` (PRIMARY KEY on id)
- `bse_details_scheme_id_bse_code_key` (UNIQUE on scheme_id, bse_code)
- `bse_details_scheme_id_fkey` (FOREIGN KEY to schemes.id)

**Indexes**:
- `idx_bse_details_scheme_id` (scheme_id)
- `idx_bse_details_bse_code` (bse_code)

---

## Advanced Multi-Table Queries

### Portfolio Analysis Query
```sql
-- Complete fund analysis with risk-return metrics
SELECT 
    s.scheme_name,
    s.amfi_broad,
    s.amfi_sub,
    s.aum_in_lakhs,
    hr.return_1y,
    hr.return_3y,
    hr.return_5y,
    risk.volatility_1y,
    risk.sharpe_ratio_1y,
    risk.maximum_drawdown_1y,
    b.sip_allowed,
    b.minimum_amount,
    b.exit_load
FROM schemes s
LEFT JOIN historical_returns hr ON s.id = hr.scheme_id 
    AND hr.return_date = (SELECT MAX(return_date) FROM historical_returns WHERE scheme_id = s.id)
LEFT JOIN historical_risk risk ON s.id = risk.scheme_id
LEFT JOIN bse_details b ON s.id = b.scheme_id
WHERE s.amfi_broad = 'Equity'
ORDER BY hr.return_1y DESC NULLS LAST;
```

### Holdings Analysis Query
```sql
-- Top holdings across fund categories
SELECT 
    s.amfi_broad,
    ch.company_name,
    COUNT(DISTINCT s.id) as funds_holding,
    ROUND(AVG(ch.percentage_holding), 2) as avg_allocation,
    ROUND(SUM(ch.market_value), 2) as total_market_value
FROM current_holdings ch
JOIN schemes s ON ch.scheme_id = s.id
GROUP BY s.amfi_broad, ch.company_name
HAVING COUNT(DISTINCT s.id) >= 5
ORDER BY s.amfi_broad, total_market_value DESC;
```

### Risk-Adjusted Performance Query
```sql
-- Best risk-adjusted returns by category
SELECT 
    s.amfi_broad,
    s.scheme_name,
    hr.return_1y,
    risk.volatility_1y,
    risk.sharpe_ratio_1y,
    risk.maximum_drawdown_1y,
    CASE 
        WHEN risk.maximum_drawdown_1y != 0 THEN hr.return_1y / ABS(risk.maximum_drawdown_1y)
        ELSE NULL 
    END as calmar_ratio
FROM schemes s
JOIN historical_returns hr ON s.id = hr.scheme_id
JOIN historical_risk risk ON s.id = risk.scheme_id
WHERE hr.return_date = (SELECT MAX(return_date) FROM historical_returns WHERE scheme_id = s.id)
    AND risk.volatility_1y IS NOT NULL
    AND hr.return_1y > 10
ORDER BY risk.sharpe_ratio_1y DESC NULLS LAST
LIMIT 20;
```

---

## Database Maintenance

### ETL Pipeline Commands
```bash
# Run complete ETL pipeline
python orchestrator.py --all

# Individual module runs
python schemes_fetcher.py
python nav_fetcher.py
python holdings_fetcher.py
python returns_calculator.py
python risk_calculator.py
python bse_details_extractor.py
```

### Backup Commands
```bash
# Full database backup
pg_dump mutual_fund > mutual_fund_backup_$(date +%Y%m%d).sql

# Schema-only backup
pg_dump --schema-only mutual_fund > mutual_fund_schema_$(date +%Y%m%d).sql
```

### Performance Optimization
- All foreign keys have optimized indexes
- Frequently queried date columns are indexed with DESC order
- UNIQUE constraints prevent duplicate records
- Batch processing with UPSERT operations for efficiency
- Connection pooling and transaction management

---

## Data Quality & Coverage

### Coverage Statistics
- **NAV Data**: 100% coverage (3.1M+ records)
- **Returns Data**: 100% coverage (3.1M+ records)
- **Risk Metrics**: 88% coverage for 1Y+ periods
- **Holdings Data**: Available for schemes with portfolio disclosure
- **BSE Trading**: 100% coverage with transaction capabilities

### Data Validation
- Foreign key constraints ensure referential integrity
- Unique constraints prevent duplicate records
- NOT NULL constraints on critical fields
- Date range validation (2006-2025)
- Numeric precision for financial calculations

### Update Frequency
- **Real-time**: Via modular ETL pipeline
- **Historical**: 19+ years of backfilled data
- **Incremental**: Daily updates for NAV and returns
- **Periodic**: Risk metrics recalculated as needed

---

*Last Updated: September 18, 2025*
*Database Version: PostgreSQL 13+*
*Total Records: 6,352,051*
*Total Size: ~3.2 GB*

**Key Tables Summary:**
- **schemes**: 1,487 mutual fund schemes (master table)
- **historical_nav**: 3,147,643 daily NAV records with daily returns
- **historical_returns**: 1,487 latest metrics per scheme
- **historical_risk**: 1,308 comprehensive risk metrics
- **fund_rankings**: 1,484 sophisticated rankings with three-pillar scoring
- **current_holdings**: 51,950 portfolio composition records
- **bse_details**: 1,487 trading and transaction details


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
    hr_sharpe.sharpe_ratio,
    sip.min_amount as min_sip,
    CASE WHEN b.exit_load_flag THEN 'Yes' ELSE 'No' END as exit_load
FROM schemes s
JOIN scheme_returns sr ON s.id = sr.scheme_id
LEFT JOIN historical_risk hr_sharpe ON s.id = hr_sharpe.scheme_id AND hr_sharpe.lookback_period_days = 252
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
    hr_sharpe.sharpe_ratio,
    sip.min_amount as min_sip,
    tc.fresh_min as min_lumpsum,
    b.exit_load_message
FROM schemes s
LEFT JOIN scheme_returns sr ON s.id = sr.scheme_id
LEFT JOIN historical_risk hr_sharpe ON s.id = hr_sharpe.scheme_id AND hr_sharpe.lookback_period_days = 252
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

---

## 8. HISTORICAL_RETURNS Table

**Purpose**: Comprehensive daily returns and rolling returns analysis for all mutual fund schemes

| Column | Type | Description |
|--------|------|-------------|
| id | SERIAL (PK) | Auto-increment primary key |
| scheme_id | TEXT (FK) | References schemes.id |
| scheme_code | TEXT | AMFI scheme code for reference |
| nav_date | DATE | Date of the return calculation |
| nav_value | DECIMAL(12,6) | Net Asset Value on the date |
| daily_return | DECIMAL(10,6) | Daily return percentage: (NAV_current / NAV_previous - 1) * 100 |
| log_return | DECIMAL(10,6) | Natural logarithm of (daily_return + 1) for risk calculations |
| rolling_return_1y | DECIMAL(10,4) | 1-year rolling return (252 trading days lookback) |
| rolling_return_3y | DECIMAL(10,4) | 3-year rolling return (756 trading days lookback) |
| rolling_return_5y | DECIMAL(10,4) | 5-year rolling return (1260 trading days lookback) |
| data_source | TEXT | Data source ('mfapi') |
| created_at | TIMESTAMP | Record creation time |
| updated_at | TIMESTAMP | Last update time |

**Indexes**: Optimized for performance analysis and time-series queries
- `idx_historical_returns_scheme_date` (scheme_id, nav_date DESC)
- `idx_historical_returns_date` (nav_date DESC)
- `idx_historical_returns_scheme_code` (scheme_code)
- `idx_historical_returns_rolling_1y` (rolling_return_1y DESC) WHERE rolling_return_1y IS NOT NULL
- `idx_historical_returns_rolling_3y` (rolling_return_3y DESC) WHERE rolling_return_3y IS NOT NULL
- `idx_historical_returns_rolling_5y` (rolling_return_5y DESC) WHERE rolling_return_5y IS NOT NULL

**Data Coverage**: 3,036,230 total records with comprehensive coverage:
- **Total Schemes**: 1,478
- **Records with 1Y Rolling**: 2,678,486 (88.22% coverage)
- **Records with 3Y Rolling**: 2,101,273 (69.21% coverage)
- **Records with 5Y Rolling**: 1,677,884 (55.26% coverage)
- **Table Size**: 1,688 MB
- **Date Range**: April 2, 2006 to September 10, 2025

**Performance Statistics**:
- Average daily return: 0.1480%
- Daily volatility: 31.72%
- Value range: -99.99% to 9921.58% (with extreme outlier handling)

**Category-wise Coverage**:
- **Equity**: 508 schemes → 1Y: 455, 3Y: 336, 5Y: 273 schemes
- **Debt**: 324 schemes → 1Y: 314, 3Y: 284, 5Y: 253 schemes  
- **Other**: 437 schemes → 1Y: 333, 3Y: 176, 5Y: 84 schemes
- **Hybrid**: 168 schemes → 1Y: 157, 3Y: 124, 5Y: 106 schemes
- **Solution Oriented**: 41 schemes → 1Y: 40, 3Y: 35, 5Y: 30 schemes

### Text-to-SQL Examples

**1. "Find top performing equity funds based on 1-year rolling returns"**
```sql
SELECT 
    s.scheme_name,
    s.amfi_sub,
    hr.nav_date,
    hr.rolling_return_1y,
    hr.nav_value,
    s.aum_in_lakhs
FROM historical_returns hr
JOIN schemes s ON hr.scheme_id = s.id
WHERE s.amfi_broad = 'Equity'
    AND hr.rolling_return_1y IS NOT NULL
    AND hr.nav_date = (
        SELECT MAX(nav_date) 
        FROM historical_returns hr2 
        WHERE hr2.scheme_id = hr.scheme_id 
        AND hr2.rolling_return_1y IS NOT NULL
    )
ORDER BY hr.rolling_return_1y DESC
LIMIT 20;
```

**2. "Show funds with consistent performance across all rolling return periods"**
```sql
SELECT 
    s.scheme_name,
    s.amfi_broad,
    s.amfi_sub,
    hr.rolling_return_1y,
    hr.rolling_return_3y,
    hr.rolling_return_5y,
    hr.nav_date as latest_date,
    s.aum_in_lakhs
FROM historical_returns hr
JOIN schemes s ON hr.scheme_id = s.id
WHERE hr.rolling_return_1y IS NOT NULL
    AND hr.rolling_return_3y IS NOT NULL
    AND hr.rolling_return_5y IS NOT NULL
    AND hr.rolling_return_1y > 15
    AND hr.rolling_return_3y > 45
    AND hr.rolling_return_5y > 75
    AND hr.nav_date = (
        SELECT MAX(nav_date) 
        FROM historical_returns hr2 
        WHERE hr2.scheme_id = hr.scheme_id 
        AND hr2.rolling_return_5y IS NOT NULL
    )
ORDER BY (hr.rolling_return_1y + hr.rolling_return_3y + hr.rolling_return_5y) DESC;
```

**3. "Find funds with lowest volatility based on daily returns over last 2 years"**
```sql
SELECT 
    s.scheme_name,
    s.amfi_broad,
    s.amfi_sub,
    COUNT(hr.daily_return) as data_points,
    ROUND(AVG(hr.daily_return), 4) as avg_daily_return,
    ROUND(STDDEV(hr.daily_return), 4) as daily_volatility,
    ROUND(AVG(hr.daily_return) * 252, 2) as annualized_return,
    ROUND(STDDEV(hr.daily_return) * SQRT(252), 2) as annualized_volatility
FROM historical_returns hr
JOIN schemes s ON hr.scheme_id = s.id
WHERE hr.nav_date >= CURRENT_DATE - INTERVAL '2 years'
    AND hr.daily_return IS NOT NULL
GROUP BY s.id, s.scheme_name, s.amfi_broad, s.amfi_sub
HAVING COUNT(hr.daily_return) >= 400
ORDER BY STDDEV(hr.daily_return)
LIMIT 15;
```

**4. "Compare rolling returns performance across fund categories"**
```sql
SELECT 
    s.amfi_broad,
    COUNT(DISTINCT hr.scheme_id) as fund_count,
    ROUND(AVG(hr.rolling_return_1y), 2) as avg_1y_rolling,
    ROUND(AVG(hr.rolling_return_3y), 2) as avg_3y_rolling,
    ROUND(AVG(hr.rolling_return_5y), 2) as avg_5y_rolling,
    ROUND(STDDEV(hr.rolling_return_1y), 2) as volatility_1y,
    ROUND(STDDEV(hr.rolling_return_3y), 2) as volatility_3y,
    ROUND(STDDEV(hr.rolling_return_5y), 2) as volatility_5y
FROM historical_returns hr
JOIN schemes s ON hr.scheme_id = s.id
WHERE hr.nav_date >= CURRENT_DATE - INTERVAL '1 year'
GROUP BY s.amfi_broad
ORDER BY avg_5y_rolling DESC NULLS LAST;
```

**5. "Identify funds with improving performance trend (3Y > 1Y rolling returns)"**
```sql
WITH latest_rolling AS (
    SELECT DISTINCT ON (hr.scheme_id)
        hr.scheme_id,
        hr.rolling_return_1y,
        hr.rolling_return_3y,
        hr.rolling_return_5y,
        hr.nav_date
    FROM historical_returns hr
    WHERE hr.rolling_return_1y IS NOT NULL 
        AND hr.rolling_return_3y IS NOT NULL
    ORDER BY hr.scheme_id, hr.nav_date DESC
)
SELECT 
    s.scheme_name,
    s.amfi_broad,
    s.amfi_sub,
    lr.rolling_return_1y,
    lr.rolling_return_3y,
    lr.rolling_return_5y,
    ROUND((lr.rolling_return_3y - lr.rolling_return_1y), 2) as performance_improvement,
    lr.nav_date as latest_date
FROM latest_rolling lr
JOIN schemes s ON lr.scheme_id = s.id
WHERE lr.rolling_return_3y > lr.rolling_return_1y
    AND lr.rolling_return_1y > 10  -- Minimum threshold
ORDER BY performance_improvement DESC
LIMIT 25;
```

**6. "Calculate Sharpe ratio using daily returns and rolling returns"**
```sql
WITH risk_metrics AS (
    SELECT 
        hr.scheme_id,
        COUNT(hr.daily_return) as data_points,
        AVG(hr.daily_return) as avg_daily_return,
        STDDEV(hr.daily_return) as daily_volatility,
        MAX(hr.rolling_return_1y) as latest_1y_rolling,
        MAX(hr.rolling_return_3y) as latest_3y_rolling
    FROM historical_returns hr
    WHERE hr.nav_date >= CURRENT_DATE - INTERVAL '1 year'
        AND hr.daily_return IS NOT NULL
    GROUP BY hr.scheme_id
    HAVING COUNT(hr.daily_return) >= 200
)
SELECT 
    s.scheme_name,
    s.amfi_broad,
    s.amfi_sub,
    rm.data_points,
    ROUND(rm.avg_daily_return * 252, 2) as annualized_return,
    ROUND(rm.daily_volatility * SQRT(252), 2) as annualized_volatility,
    ROUND(rm.latest_1y_rolling, 2) as rolling_1y_return,
    ROUND(rm.latest_3y_rolling, 2) as rolling_3y_return,
    ROUND(
        CASE 
            WHEN rm.daily_volatility > 0 THEN 
                (rm.avg_daily_return * 252 - 6) / (rm.daily_volatility * SQRT(252))
            ELSE NULL 
        END, 3
    ) as calculated_sharpe_ratio
FROM risk_metrics rm
JOIN schemes s ON rm.scheme_id = s.id
WHERE rm.daily_volatility > 0
ORDER BY calculated_sharpe_ratio DESC NULLS LAST
LIMIT 20;
```

**7. "Find funds that performed well during market downturns (negative daily returns)"**
```sql
WITH downturn_performance AS (
    SELECT 
        hr.scheme_id,
        COUNT(CASE WHEN hr.daily_return < 0 THEN 1 END) as negative_days,
        COUNT(hr.daily_return) as total_days,
        AVG(CASE WHEN hr.daily_return < 0 THEN hr.daily_return END) as avg_negative_return,
        AVG(hr.daily_return) as overall_avg_return,
        MIN(hr.daily_return) as worst_single_day
    FROM historical_returns hr
    WHERE hr.nav_date >= CURRENT_DATE - INTERVAL '2 years'
        AND hr.daily_return IS NOT NULL
    GROUP BY hr.scheme_id
    HAVING COUNT(hr.daily_return) >= 300
)
SELECT 
    s.scheme_name,
    s.amfi_broad,
    s.amfi_sub,
    dp.total_days,
    dp.negative_days,
    ROUND((dp.negative_days::float / dp.total_days * 100), 1) as negative_days_pct,
    ROUND(dp.avg_negative_return, 4) as avg_loss_on_bad_days,
    ROUND(dp.overall_avg_return, 4) as overall_avg_daily_return,
    ROUND(dp.worst_single_day, 4) as worst_single_day_loss
FROM downturn_performance dp
JOIN schemes s ON dp.scheme_id = s.id
WHERE dp.avg_negative_return > -2.0  -- Less than 2% average loss on bad days
ORDER BY dp.avg_negative_return DESC
LIMIT 20;
```

**8. "Track rolling returns evolution over time for specific fund categories"**
```sql
SELECT 
    DATE_TRUNC('month', hr.nav_date) as month_year,
    s.amfi_broad,
    COUNT(DISTINCT hr.scheme_id) as funds_with_data,
    ROUND(AVG(hr.rolling_return_1y), 2) as avg_1y_rolling,
    ROUND(AVG(hr.rolling_return_3y), 2) as avg_3y_rolling,
    ROUND(PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY hr.rolling_return_1y), 2) as median_1y_rolling,
    ROUND(PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY hr.rolling_return_1y), 2) as top_quartile_1y,
    ROUND(PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY hr.rolling_return_1y), 2) as bottom_quartile_1y
FROM historical_returns hr
JOIN schemes s ON hr.scheme_id = s.id
WHERE hr.nav_date >= CURRENT_DATE - INTERVAL '3 years'
    AND hr.rolling_return_1y IS NOT NULL
    AND s.amfi_broad IN ('Equity', 'Debt', 'Hybrid')
    AND hr.maximum_drawdown IS NOT NULL
    AND hr.annualized_volatility IS NOT NULL
    AND hr.avg_daily_return * 252 > 8  -- Minimum 8% annualized return
ORDER BY calmar_ratio DESC NULLS LAST
LIMIT 25;
```

**10. "Find funds with lowest tail risk (best VaR 95%) by category"**
```sql
WITH ranked_var AS (
    SELECT 
        s.scheme_name,
        s.amfi_broad,
        s.amfi_sub,
        hr.lookback_period_years,
        ROUND(hr.var_95_1day * 100, 2) as var_95_percent,
        ROUND(hr.annualized_volatility, 4) as volatility_percent,
        ROUND(hr.maximum_drawdown, 2) as max_drawdown_percent,
        ROW_NUMBER() OVER (PARTITION BY s.amfi_broad ORDER BY hr.var_95_1day DESC) as var_rank
    FROM historical_risk hr
    JOIN schemes s ON hr.scheme_id = s.id
    WHERE hr.lookback_period_years = 1.00
        AND hr.var_95_1day IS NOT NULL
)
SELECT 
    scheme_name,
    amfi_broad,
    amfi_sub,
    var_95_percent,
    volatility_percent,
    max_drawdown_percent
FROM ranked_var
WHERE var_rank <= 5
ORDER BY amfi_broad, var_rank;
```

**11. "Analyze correlation between daily returns and rolling returns"**
```sql
WITH correlation_analysis AS (
    SELECT 
        hr.scheme_id,
        COUNT(*) as data_points,
        CORR(hr.daily_return, hr.rolling_return_1y) as daily_vs_1y_correlation,
        CORR(hr.rolling_return_1y, hr.rolling_return_3y) as rolling_1y_vs_3y_correlation,
        AVG(hr.daily_return) as avg_daily_return,
        AVG(hr.rolling_return_1y) as avg_1y_rolling,
        AVG(hr.rolling_return_3y) as avg_3y_rolling
    FROM historical_returns hr
    WHERE hr.nav_date >= CURRENT_DATE - INTERVAL '1 year'
        AND hr.daily_return IS NOT NULL
        AND hr.rolling_return_1y IS NOT NULL
    GROUP BY hr.scheme_id
    HAVING COUNT(*) >= 200
)
SELECT 
    s.scheme_name,
    s.amfi_broad,
    s.amfi_sub,
    ca.data_points,
    ROUND(ca.daily_vs_1y_correlation::numeric, 3) as daily_vs_rolling_correlation,
    ROUND(ca.rolling_1y_vs_3y_correlation::numeric, 3) as short_vs_long_rolling_correlation,
    ROUND(ca.avg_daily_return * 252, 2) as annualized_daily_return,
    ROUND(ca.avg_1y_rolling, 2) as avg_1y_rolling_return,
    ROUND(ca.avg_3y_rolling, 2) as avg_3y_rolling_return
FROM correlation_analysis ca
JOIN schemes s ON ca.scheme_id = s.id
ORDER BY ca.rolling_1y_vs_3y_correlation DESC NULLS LAST
LIMIT 20;
```

---

## 9. HISTORICAL_RISK Table

**Purpose**: Comprehensive risk metrics and volatility analysis for mutual fund schemes

| Column | Type | Description |
|--------|------|-------------|
| id | SERIAL (PK) | Auto-increment primary key |
| scheme_id | TEXT (FK) | References schemes.id |
| scheme_code | TEXT | AMFI scheme code for reference |
| calculation_date | DATE | Date of risk calculation (latest available data date) |
| lookback_period_days | INTEGER | Number of days used for calculation (252, 504, 756, 1260) |
| lookback_period_years | DECIMAL(4,2) | Lookback period in years: calculated as lookback_period_days / 252 |
| data_points | INTEGER | Actual number of data points used in calculation |
| annualized_volatility | DECIMAL(10,6) | Annualized volatility: stddev(daily_returns) * sqrt(252) |
| avg_daily_return | DECIMAL(10,6) | Average daily return over the lookback period |
| min_daily_return | DECIMAL(10,6) | Minimum daily return in the period |
| max_daily_return | DECIMAL(10,6) | Maximum daily return in the period |
| maximum_drawdown | DECIMAL(10,6) | Maximum drawdown: worst peak-to-trough loss as negative percentage |
| var_95_1day | DECIMAL(10,6) | 1-day 95% Value at Risk: 5th percentile of daily returns using historical simulation |
| sharpe_ratio | DECIMAL(10,6) | Sharpe Ratio: (Portfolio Return - Risk-free Rate) / Standard Deviation of Returns |
| sortino_ratio | DECIMAL(10,6) | Sortino Ratio: (Portfolio Return - Risk-free Rate) / Downside Deviation |
| skewness | DECIMAL(10,6) | Skewness of daily returns distribution |
| kurtosis | DECIMAL(10,6) | Kurtosis of daily returns distribution |
| **beta** | **DECIMAL(10,6)** | **Category Beta: Correlation with peer group average (category benchmark)** |
| **alpha** | **DECIMAL(10,6)** | **Category Alpha: Jensen's Alpha relative to category peer average** |
| **information_ratio** | **DECIMAL(10,6)** | **Information Ratio: Alpha / Tracking Error relative to category benchmark** |
| **benchmark_category** | **VARCHAR(50)** | **Category benchmark used (e.g., 'Equity_peer_average', 'Debt_peer_average')** |
| **index_beta** | **DECIMAL(10,6)** | **Index Beta: Correlation with appropriate index fund proxy** |
| **index_alpha** | **DECIMAL(10,6)** | **Index Alpha: Jensen's Alpha relative to index fund proxy** |
| **index_benchmark** | **VARCHAR(100)** | **Index fund proxy used as benchmark (e.g., 'Axis Nifty 100 Index Fund - Growth')** |
| data_source | TEXT | Data source ('calculated') |
| created_at | TIMESTAMP | Record creation time |
| updated_at | TIMESTAMP | Last update time |

**Indexes**: Optimized for risk analysis and volatility queries
- `idx_historical_risk_scheme_id` (scheme_id)
- `idx_historical_risk_calculation_date` (calculation_date DESC)
- `idx_historical_risk_scheme_date` (scheme_id, calculation_date DESC)
- `idx_historical_risk_volatility` (annualized_volatility DESC) WHERE annualized_volatility IS NOT NULL
- `idx_historical_risk_max_drawdown` (maximum_drawdown DESC) WHERE maximum_drawdown IS NOT NULL
- `idx_historical_risk_var_95` (var_95_1day) WHERE var_95_1day IS NOT NULL
- `idx_historical_risk_sharpe_ratio` (sharpe_ratio DESC) WHERE sharpe_ratio IS NOT NULL
- `idx_historical_risk_sortino_ratio` (sortino_ratio DESC) WHERE sortino_ratio IS NOT NULL
- `idx_historical_risk_lookback` (lookback_period_days)
- `idx_historical_risk_lookback_years` (lookback_period_years)
- **`idx_historical_risk_beta` (beta DESC) WHERE beta IS NOT NULL**
- **`idx_historical_risk_alpha` (alpha DESC) WHERE alpha IS NOT NULL**
- **`idx_historical_risk_information_ratio` (information_ratio DESC) WHERE information_ratio IS NOT NULL**
- **`idx_historical_risk_benchmark_category` (benchmark_category)**
- **`idx_historical_risk_index_beta` (index_beta DESC) WHERE index_beta IS NOT NULL**
- **`idx_historical_risk_index_alpha` (index_alpha DESC) WHERE index_alpha IS NOT NULL**
- **`idx_historical_risk_index_benchmark` (index_benchmark)**

**Data Coverage**: 4,155+ total records with comprehensive risk metrics:
- **Total Schemes**: 1,300+ schemes with risk data
- **Lookback Periods**: 4 periods (1Y, 2Y, 3Y, 5Y)
- **Date Range**: September 9-10, 2025
- **Records with Volatility**: 4,155 (100% coverage)
- **Volatility Range**: 0.0005% to 4.0255%
- **Records with Category Beta/Alpha**: 1,379+ (category-relative performance metrics)
- **Records with Index Beta/Alpha**: 1,379+ (index-relative performance metrics)

**Risk Statistics by Category (1Y Period)**:
- **Equity**: Avg volatility 0.1553%, Avg max drawdown -18.54%, 455 schemes
- **Debt**: Avg volatility 0.0119%, Avg max drawdown -0.94%, 314 schemes
- **Hybrid**: Avg volatility 0.0641%, Avg max drawdown -6.70%, 157 schemes
- **Other**: Avg volatility 0.1191%, Avg max drawdown -11.81%, 334 schemes
- **Solution Oriented**: Avg volatility 0.0987%, Avg max drawdown -11.66%, 40 schemes

**Maximum Drawdown Statistics**:
- **Records with Drawdown**: 4,155 (100% coverage)
- **Average Maximum Drawdown**: -18.26%
- **Worst Maximum Drawdown**: -83.04% (JM Value Fund - 5Y period)
- **Drawdown Range by Period**: 1Y: -0.94% to -18.54%, 5Y: -3.44% to -46.67%

**Value at Risk (VaR) 95% Statistics**:
- **Records with VaR**: 4,155 (100% coverage)
- **Method**: Historical Simulation (Non-parametric)
- **Average VaR by Period**: 1Y: -1.07%, 2Y: -0.94%, 3Y: -0.87%, 5Y: -0.81%
- **Worst VaR**: -3.87% (Edelweiss US Technology Equity Fund - 1Y period)
- **VaR Range by Period**: 1Y: -3.87% to 0.01%, 5Y: -3.01% to 0.01%

**Sharpe & Sortino Ratio Statistics**:
- **Records with Ratios**: 4,155 (100% coverage)
- **Risk-free Rate**: 6% (Indian Government Bonds)
- **Average Sharpe Ratio by Period**: 1Y: 0.167, 2Y: 0.537, 3Y: 0.802, 5Y: 0.250
- **Best Sharpe Ratio**: 4.373 (Aditya Birla Sun Life Money Manager Fund - 1Y period)
- **Best Sortino Ratio**: 10.000 (Multiple debt funds with minimal downside risk)

**Category Beta/Alpha Statistics** (Peer Group Benchmarking):
- **Records with Category Beta**: 1,379+ (relative to category peer averages)
- **Records with Category Alpha**: 1,379+ (Jensen's Alpha vs peer group)
- **Records with Information Ratio**: 1,379+ (Alpha / Tracking Error vs peers)
- **Benchmark Categories**: Equity_peer_average, Debt_peer_average, Hybrid_peer_average, etc.
- **Beta Range**: Typically -5.0 to +5.0 (capped for database stability)
- **Alpha Range**: Typically -1.0 to +1.0 (annualized excess returns)

**Index Beta/Alpha Statistics** (Index Fund Benchmarking):
- **Records with Index Beta**: 1,379+ (relative to appropriate index fund proxies)
- **Records with Index Alpha**: 1,379+ (Jensen's Alpha vs index benchmarks)
- **Index Benchmarks Used**:
  - Large Cap → Axis Nifty 100 Index Fund - Growth
  - Mid Cap → Motilal Oswal Nifty Midcap 150 Index Fund
  - Small Cap → Nippon India Nifty Smallcap 250 Index Fund Growth
  - Multi Cap → HDFC NIFTY500 Multicap 50 25 25 Index Fund
  - Debt Funds → HDFC Nifty PSU Bond Plus SDL Index Fund - Growth
  - Hybrid/Other → Motilal Oswal Nifty 500 Index Fund
- **Index Beta Range**: Typically -5.0 to +5.0 (correlation with index proxy)
- **Index Alpha Range**: Typically -1.0 to +1.0 (excess return vs index)

### Text-to-SQL Examples

**1. "Find funds with best category-relative performance (highest alpha vs peers)"**
```sql
SELECT 
    s.scheme_name,
    s.amfi_broad,
    s.amfi_sub,
    hr.lookback_period_years,
    ROUND(hr.alpha, 4) as category_alpha,
    ROUND(hr.beta, 4) as category_beta,
    ROUND(hr.information_ratio, 4) as info_ratio,
    hr.benchmark_category
FROM historical_risk hr
JOIN schemes s ON hr.scheme_id = s.id
WHERE hr.alpha IS NOT NULL
    AND hr.lookback_period_days = 252  -- 1 year
ORDER BY hr.alpha DESC
LIMIT 20;
```

**2. "Compare category vs index performance for equity funds"**
```sql
SELECT 
    s.scheme_name,
    s.amfi_sub,
    hr.lookback_period_years,
    ROUND(hr.alpha, 4) as category_alpha,
    ROUND(hr.beta, 4) as category_beta,
    ROUND(hr.index_alpha, 4) as index_alpha,
    ROUND(hr.index_beta, 4) as index_beta,
    hr.benchmark_category,
    hr.index_benchmark
FROM historical_risk hr
JOIN schemes s ON hr.scheme_id = s.id
WHERE s.amfi_broad = 'Equity'
    AND hr.alpha IS NOT NULL
    AND hr.index_alpha IS NOT NULL
    AND hr.lookback_period_days = 252
ORDER BY hr.index_alpha DESC
LIMIT 15;
```

**3. "Find funds outperforming both peers and index benchmarks"**
```sql
SELECT 
    s.scheme_name,
    s.amfi_broad,
    s.amfi_sub,
    ROUND(hr.alpha, 4) as category_alpha,
    ROUND(hr.index_alpha, 4) as index_alpha,
    ROUND(hr.information_ratio, 4) as info_ratio,
    hr.benchmark_category,
    hr.index_benchmark
FROM historical_risk hr
JOIN schemes s ON hr.scheme_id = s.id
WHERE hr.alpha > 0.05  -- Positive category alpha
    AND hr.index_alpha > 0.05  -- Positive index alpha
    AND hr.lookback_period_days = 252
ORDER BY (hr.alpha + hr.index_alpha) DESC
LIMIT 25;
```

**4. "Analyze beta consistency across different benchmarks"**
```sql
SELECT 
    s.scheme_name,
    s.amfi_broad,
    s.amfi_sub,
    hr.lookback_period_years,
    ROUND(hr.beta, 4) as category_beta,
    ROUND(hr.index_beta, 4) as index_beta,
    ROUND(ABS(hr.beta - hr.index_beta), 4) as beta_difference,
    hr.benchmark_category,
    hr.index_benchmark
FROM historical_risk hr
JOIN schemes s ON hr.scheme_id = s.id
WHERE hr.beta IS NOT NULL
    AND hr.index_beta IS NOT NULL
    AND hr.lookback_period_days = 252
ORDER BY beta_difference
LIMIT 20;
```

**5. "Find funds with best capital preservation (lowest maximum drawdown) in each category"**
```sql
WITH ranked_drawdown AS (
    SELECT 
        s.scheme_name,
        s.amfi_broad,
        s.amfi_sub,
        hr.maximum_drawdown,
        hr.annualized_volatility,
        hr.avg_daily_return,
        hr.data_points,
        ROW_NUMBER() OVER (PARTITION BY s.amfi_broad ORDER BY hr.maximum_drawdown DESC) as drawdown_rank
    FROM historical_risk hr
    JOIN schemes s ON hr.scheme_id = s.id
    WHERE hr.lookback_period_days = 252
        AND hr.maximum_drawdown IS NOT NULL
)
SELECT 
    scheme_name,
    amfi_broad,
    amfi_sub,
    ROUND(maximum_drawdown, 2) as max_drawdown_pct,
    ROUND(annualized_volatility, 4) as volatility_pct,
    ROUND(avg_daily_return * 252, 2) as annualized_return_pct,
    data_points
FROM ranked_drawdown
WHERE drawdown_rank <= 5
ORDER BY amfi_broad, drawdown_rank;
```

**2. "Compare risk-adjusted returns across different lookback periods"**
```sql
SELECT 
    s.scheme_name,
    s.amfi_broad,
    hr.lookback_period_days / 252.0 as period_years,
    ROUND(hr.annualized_volatility, 4) as volatility_pct,
    ROUND(hr.avg_daily_return * 252, 2) as annualized_return_pct,
    ROUND(
        CASE 
            WHEN hr.annualized_volatility > 0 THEN 
                (hr.avg_daily_return * 252 - 6) / hr.annualized_volatility
            ELSE NULL 
        END, 3
    ) as risk_adjusted_ratio,
    hr.data_points
FROM historical_risk hr
JOIN schemes s ON hr.scheme_id = s.id
WHERE s.amfi_broad = 'Equity'
    AND hr.annualized_volatility IS NOT NULL
    AND hr.avg_daily_return * 252 > 10  -- Minimum 10% annualized return
ORDER BY risk_adjusted_ratio DESC NULLS LAST
LIMIT 20;
```

**3. "Identify funds with extreme return distributions (high skewness/kurtosis)"**
```sql
SELECT 
    s.scheme_name,
    s.amfi_broad,
    s.amfi_sub,
    hr.lookback_period_years as period_years,
    ROUND(hr.annualized_volatility, 4) as volatility_pct,
    ROUND(hr.skewness, 3) as skewness,
    ROUND(hr.kurtosis, 3) as kurtosis,
    ROUND(hr.min_daily_return, 4) as worst_day_pct,
    ROUND(hr.max_daily_return, 4) as best_day_pct,
    hr.data_points
FROM historical_risk hr
JOIN schemes s ON hr.scheme_id = s.id
WHERE hr.lookback_period_days = 252
    AND (ABS(hr.skewness) > 1.5 OR ABS(hr.kurtosis) > 5)
    AND hr.annualized_volatility IS NOT NULL
ORDER BY ABS(hr.skewness) + ABS(hr.kurtosis) DESC
LIMIT 25;
```

**4. "Find funds with consistent volatility across different time periods"**
```sql
WITH volatility_consistency AS (
    SELECT 
        hr.scheme_id,
        COUNT(*) as period_count,
        STDDEV(hr.annualized_volatility) as volatility_stddev,
        AVG(hr.annualized_volatility) as avg_volatility,
        MIN(hr.annualized_volatility) as min_volatility,
        MAX(hr.annualized_volatility) as max_volatility
    FROM historical_risk hr
    WHERE hr.annualized_volatility IS NOT NULL
    GROUP BY hr.scheme_id
    HAVING COUNT(*) >= 3  -- At least 3 different periods
)
SELECT 
    s.scheme_name,
    s.amfi_broad,
    s.amfi_sub,
    vc.period_count,
    ROUND(vc.avg_volatility, 4) as avg_volatility_pct,
    ROUND(vc.volatility_stddev, 4) as volatility_consistency,
    ROUND(vc.min_volatility, 4) as min_volatility_pct,
    ROUND(vc.max_volatility, 4) as max_volatility_pct,
    ROUND((vc.max_volatility - vc.min_volatility) / vc.avg_volatility * 100, 1) as volatility_range_pct
FROM volatility_consistency vc
JOIN schemes s ON vc.scheme_id = s.id
WHERE vc.volatility_stddev < vc.avg_volatility * 0.2  -- Low volatility variation
ORDER BY vc.volatility_stddev
LIMIT 20;
```

**5. "Analyze volatility patterns by fund category and time horizon"**
```sql
SELECT 
    s.amfi_broad,
    hr.lookback_period_days / 252.0 as period_years,
    COUNT(*) as fund_count,
    ROUND(AVG(hr.annualized_volatility), 4) as avg_volatility,
    ROUND(STDDEV(hr.annualized_volatility), 4) as volatility_dispersion,
    ROUND(MIN(hr.annualized_volatility), 4) as min_volatility,
    ROUND(MAX(hr.annualized_volatility), 4) as max_volatility,
    ROUND(PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY hr.annualized_volatility), 4) as q1_volatility,
    ROUND(PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY hr.annualized_volatility), 4) as median_volatility,
    ROUND(PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY hr.annualized_volatility), 4) as q3_volatility
FROM historical_risk hr
JOIN schemes s ON hr.scheme_id = s.id
WHERE hr.annualized_volatility IS NOT NULL
GROUP BY s.amfi_broad, hr.lookback_period_days
ORDER BY s.amfi_broad, period_years;
```

**6. "Find funds with best downside protection (low negative skewness, controlled max loss)"**
```sql
SELECT 
    s.scheme_name,
    s.amfi_broad,
    s.amfi_sub,
    ROUND(hr.annualized_volatility, 4) as volatility_pct,
    ROUND(hr.avg_daily_return * 252, 2) as annualized_return_pct,
    ROUND(hr.skewness, 3) as skewness,
    ROUND(hr.min_daily_return, 4) as worst_day_pct,
    ROUND(hr.max_daily_return, 4) as best_day_pct,
    ROUND(ABS(hr.min_daily_return) / hr.max_daily_return, 2) as downside_upside_ratio,
    hr.data_points
FROM historical_risk hr
JOIN schemes s ON hr.scheme_id = s.id
WHERE hr.lookback_period_days = 252
    AND hr.skewness > -0.5  -- Not too negatively skewed
    AND hr.min_daily_return > -5.0  -- Max loss less than 5% in a day
    AND hr.annualized_volatility IS NOT NULL
    AND hr.avg_daily_return > 0  -- Positive average returns
ORDER BY hr.skewness DESC, hr.min_daily_return DESC
LIMIT 25;
```

**7. "Calculate Value at Risk (VaR) approximation using volatility"**
```sql
SELECT 
    s.scheme_name,
    s.amfi_broad,
    s.amfi_sub,
    ROUND(hr.annualized_volatility, 4) as annual_volatility_pct,
    ROUND(hr.avg_daily_return * 252, 2) as expected_annual_return_pct,
    -- 1-day VaR at 95% confidence (1.645 * daily_volatility)
    ROUND(1.645 * (hr.annualized_volatility / SQRT(252)), 4) as var_1day_95_pct,
    -- 1-day VaR at 99% confidence (2.33 * daily_volatility)
    ROUND(2.33 * (hr.annualized_volatility / SQRT(252)), 4) as var_1day_99_pct,
    -- Monthly VaR at 95% confidence
    ROUND(1.645 * (hr.annualized_volatility / SQRT(12)), 4) as var_1month_95_pct,
    hr.data_points
FROM historical_risk hr
JOIN schemes s ON hr.scheme_id = s.id
WHERE hr.lookback_period_days = 252
    AND hr.annualized_volatility IS NOT NULL
    AND s.amfi_broad IN ('Equity', 'Hybrid')
ORDER BY hr.annualized_volatility DESC
LIMIT 20;
```

**8. "Compare actual vs predicted volatility using different time horizons"**
```sql
WITH volatility_comparison AS (
    SELECT 
        hr1.scheme_id,
        hr1.annualized_volatility as vol_1y,
        hr2.annualized_volatility as vol_2y,
        hr3.annualized_volatility as vol_3y,
        hr5.annualized_volatility as vol_5y
    FROM historical_risk hr1
    LEFT JOIN historical_risk hr2 ON hr1.scheme_id = hr2.scheme_id AND hr2.lookback_period_days = 504
    LEFT JOIN historical_risk hr3 ON hr1.scheme_id = hr3.scheme_id AND hr3.lookback_period_days = 756
    LEFT JOIN historical_risk hr5 ON hr1.scheme_id = hr5.scheme_id AND hr5.lookback_period_days = 1260
    WHERE hr1.lookback_period_days = 252
)
SELECT 
    s.scheme_name,
    s.amfi_broad,
    ROUND(vc.vol_1y, 4) as volatility_1y,
    ROUND(vc.vol_2y, 4) as volatility_2y,
    ROUND(vc.vol_3y, 4) as volatility_3y,
    ROUND(vc.vol_5y, 4) as volatility_5y,
    ROUND(STDDEV(val.volatility), 4) as volatility_stability
FROM volatility_comparison vc
JOIN schemes s ON vc.scheme_id = s.id
CROSS JOIN LATERAL (
    VALUES (vc.vol_1y), (vc.vol_2y), (vc.vol_3y), (vc.vol_5y)
) AS val(volatility)
WHERE vc.vol_1y IS NOT NULL 
    AND vc.vol_2y IS NOT NULL 
    AND vc.vol_3y IS NOT NULL
GROUP BY s.scheme_name, s.amfi_broad, vc.vol_1y, vc.vol_2y, vc.vol_3y, vc.vol_5y
ORDER BY volatility_stability
LIMIT 20;
```

### Capture Ratio Analysis Examples

**1. "Find funds with best up-capture and down-capture ratios"**
```sql
SELECT 
    s.scheme_name,
    s.amfi_broad,
    s.amfi_sub,
    ROUND(hr.up_capture_ratio_3y * 100, 2) as up_capture_pct,
    ROUND(hr.down_capture_ratio_3y * 100, 2) as down_capture_pct,
    ROUND((hr.up_capture_ratio_3y / hr.down_capture_ratio_3y), 2) as capture_ratio_efficiency,
    CASE 
        WHEN hr.up_capture_ratio_3y > 1.0 AND hr.down_capture_ratio_3y < 1.0 THEN 'Excellent'
        WHEN hr.up_capture_ratio_3y > 0.9 AND hr.down_capture_ratio_3y < 0.9 THEN 'Good'
        WHEN hr.up_capture_ratio_3y > 0.8 THEN 'Average'
        ELSE 'Below Average'
    END as capture_rating
FROM historical_risk hr
JOIN schemes s ON hr.scheme_id = s.id
WHERE hr.up_capture_ratio_3y IS NOT NULL 
    AND hr.down_capture_ratio_3y IS NOT NULL
    AND s.amfi_broad = 'Equity'
ORDER BY capture_ratio_efficiency DESC
LIMIT 20;
```

**2. "Compare capture ratios across fund categories"**
```sql
SELECT 
    s.amfi_sub as fund_category,
    COUNT(*) as fund_count,
    ROUND(AVG(hr.up_capture_ratio_3y) * 100, 2) as avg_up_capture_pct,
    ROUND(AVG(hr.down_capture_ratio_3y) * 100, 2) as avg_down_capture_pct,
    ROUND(PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY hr.up_capture_ratio_3y) * 100, 2) as median_up_capture_pct,
    ROUND(PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY hr.down_capture_ratio_3y) * 100, 2) as median_down_capture_pct,
    ROUND(AVG(hr.up_capture_ratio_3y / hr.down_capture_ratio_3y), 2) as avg_efficiency_ratio
FROM historical_risk hr
JOIN schemes s ON hr.scheme_id = s.id
WHERE hr.up_capture_ratio_3y IS NOT NULL 
    AND hr.down_capture_ratio_3y IS NOT NULL
    AND s.amfi_broad IN ('Equity', 'Hybrid')
GROUP BY s.amfi_sub
HAVING COUNT(*) >= 5
ORDER BY avg_efficiency_ratio DESC;
```

**3. "Identify defensive funds with low down-capture ratios"**
```sql
SELECT 
    s.scheme_name,
    s.amfi_sub,
    ROUND(hr.up_capture_ratio_3y * 100, 2) as up_capture_pct,
    ROUND(hr.down_capture_ratio_3y * 100, 2) as down_capture_pct,
    ROUND(hr.volatility_3y * 100, 2) as volatility_3y_pct,
    ROUND(hr.sharpe_ratio_3y, 3) as sharpe_3y,
    ROUND(hr.maximum_drawdown_3y * 100, 2) as max_drawdown_3y_pct
FROM historical_risk hr
JOIN schemes s ON hr.scheme_id = s.id
WHERE hr.down_capture_ratio_3y < 0.8  -- Low down-capture (defensive)
    AND hr.up_capture_ratio_3y > 0.7   -- Reasonable up-capture
    AND hr.volatility_3y IS NOT NULL
    AND s.amfi_broad = 'Equity'
ORDER BY hr.down_capture_ratio_3y ASC, hr.up_capture_ratio_3y DESC
LIMIT 15;
```

**4. "Comprehensive risk-return analysis with capture ratios"**
```sql
SELECT 
    s.scheme_name,
    s.amfi_broad,
    ROUND(sr.return_3y, 2) as return_3y_pct,
    ROUND(hr.volatility_3y * 100, 2) as volatility_3y_pct,
    ROUND(hr.sharpe_ratio_3y, 3) as sharpe_3y,
    ROUND(hr.up_capture_ratio_3y * 100, 2) as up_capture_pct,
    ROUND(hr.down_capture_ratio_3y * 100, 2) as down_capture_pct,
    ROUND(hr.maximum_drawdown_3y * 100, 2) as max_drawdown_pct,
    CASE 
        WHEN hr.up_capture_ratio_3y > 1.0 AND hr.down_capture_ratio_3y < 0.8 THEN 'Aggressive Upside, Defensive Downside'
        WHEN hr.up_capture_ratio_3y > 0.9 AND hr.down_capture_ratio_3y < 0.9 THEN 'Balanced Capture'
        WHEN hr.up_capture_ratio_3y < 0.8 AND hr.down_capture_ratio_3y < 0.8 THEN 'Conservative Both Ways'
        WHEN hr.up_capture_ratio_3y > 1.0 AND hr.down_capture_ratio_3y > 1.0 THEN 'High Beta Style'
        ELSE 'Mixed Performance'
    END as capture_style
FROM schemes s
JOIN scheme_returns sr ON s.id = sr.scheme_id
JOIN historical_risk hr ON s.id = hr.scheme_id
WHERE hr.up_capture_ratio_3y IS NOT NULL 
    AND hr.down_capture_ratio_3y IS NOT NULL
    AND sr.return_3y IS NOT NULL
    AND s.amfi_broad = 'Equity'
ORDER BY (hr.up_capture_ratio_3y / hr.down_capture_ratio_3y) DESC
LIMIT 25;
```

---

## 10. HISTORICAL_NAV Table (Legacy Reference)

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

---

## Advanced Multi-Table Analysis Queries

### Portfolio Performance with Rolling Returns
```sql
-- Build a comprehensive portfolio analysis using rolling returns
SELECT 
    s.amfi_broad,
    s.scheme_name,
    s.risk_level,
    hr.rolling_return_1y,
    hr.rolling_return_3y,
    hr.rolling_return_5y,
    hr.daily_return,
    sip.min_amount as min_sip,
    CASE WHEN b.exit_load_flag THEN 'Yes' ELSE 'No' END as exit_load,
    s.aum_in_lakhs
FROM schemes s
JOIN historical_returns hr ON s.id = hr.scheme_id
LEFT JOIN bse_details b ON s.id = b.scheme_id
LEFT JOIN sip_configurations sip ON b.id = sip.bse_detail_id
WHERE s.sip_allowed = true 
    AND hr.rolling_return_1y IS NOT NULL
    AND hr.nav_date = (
        SELECT MAX(nav_date) 
        FROM historical_returns hr2 
        WHERE hr2.scheme_id = hr.scheme_id 
        AND hr2.rolling_return_1y IS NOT NULL
    )
    AND hr.rolling_return_1y > 15
    AND s.risk_level BETWEEN 2 AND 4
ORDER BY s.amfi_broad, hr.rolling_return_5y DESC NULLS LAST;
```

### Complete Investment Platform Query
```sql
-- Complete fund information for investment platform with rolling returns
SELECT 
    s.scheme_name,
    s.amfi_broad || ' - ' || s.amfi_sub as category,
    s.current_nav,
    s.aum_in_lakhs,
    s.risk_level,
    sr.yrs1, sr.yrs3, sr.yrs5,
    hr.rolling_return_1y,
    hr.rolling_return_3y,
    hr.rolling_return_5y,
    hr.daily_return as latest_daily_return,
    hr_sharpe.sharpe_ratio,
    sip.min_amount as min_sip,
    tc.fresh_min as min_lumpsum,
    b.exit_load_message
FROM schemes s
LEFT JOIN scheme_returns sr ON s.id = sr.scheme_id
LEFT JOIN historical_returns hr ON s.id = hr.scheme_id AND hr.nav_date = (
    SELECT MAX(nav_date) FROM historical_returns hr2 WHERE hr2.scheme_id = hr.scheme_id
)
LEFT JOIN historical_risk hr_sharpe ON s.id = hr_sharpe.scheme_id AND hr_sharpe.lookback_period_days = 252
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

# Calculate historical returns and rolling returns
python3 calculate_historical_returns.py
python3 add_rolling_returns_complete.py

# Calculate risk metrics and volatility
python3 create_historical_risk_table.py

# Add maximum drawdown calculations
python3 add_maximum_drawdown.py

# Add lookback period in years column
python3 add_lookback_years_column.py

# Add Value at Risk (VaR) 95% calculations
python3 add_var_95_column.py

# Add Sharpe and Sortino ratio calculations
python3 add_sharpe_sortino_ratios.py

# Add capture ratio calculations
python3 add_capture_ratios.py
```

### Backup Command
```bash
pg_dump mutual_fund > mutual_fund_backup_$(date +%Y%m%d).sql
```

### Performance Optimization
- All foreign keys have indexes
- Frequently queried columns are indexed
- JSONB columns support GIN indexes for array operations
- Rolling returns columns have conditional indexes for performance
- Time-series queries optimized with date-based partitioning considerations

---

*Last Updated: September 18, 2025*
*Total Records: 6,352,051 across 8 core tables*

**Complete Database Coverage:**
- **3,147,643** historical NAV records with daily returns (19+ years: 2006-2025)
- **1,487** latest return metrics (one per scheme)
- **1,484** sophisticated fund rankings with three-pillar scoring
- **1,308** comprehensive risk metrics
- **51,950** current portfolio holdings
- **1,487** BSE trading details

*Data Sources: MF APIs Club (https://app.mfapis.club) + MFApi.in (https://api.mfapi.in)*
*Ranking Algorithm: Three-pillar thematic factor grouping with percentile normalization*
