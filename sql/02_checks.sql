-- Data checks. Each check is counted; the action says what happens to the rows or columns found.
CREATE OR REPLACE TABLE data_checks AS
WITH s AS (SELECT * FROM stg_employees)
SELECT * FROM (VALUES
    (1, 'Rows with a missing value in any column',
        (SELECT count(*) FROM s) - (SELECT count(*) FROM s WHERE COLUMNS(*) IS NOT NULL), 'rows', 'none found; nothing to impute'),
    (2, 'Duplicate employee numbers',
        (SELECT count(*) - count(DISTINCT employee_number) FROM s), 'rows', 'none found'),
    (3, 'Records identical apart from the employee number',
        (SELECT count(*) FROM (SELECT * EXCLUDE (employee_number), count(*) AS n FROM s GROUP BY ALL HAVING n > 1)),
        'groups', 'none found'),
    (4, 'Columns with one value for every employee (employee count, over 18, standard hours)',
        (SELECT (count(DISTINCT employee_count) = 1)::INT + (count(DISTINCT over18) = 1)::INT
              + (count(DISTINCT standard_hours) = 1)::INT FROM s), 'columns', 'dropped: they carry no information'),
    (5, 'Years in current role greater than years at the company',
        (SELECT count(*) FROM s WHERE years_in_current_role > years_at_company), 'rows', 'kept, flagged'),
    (6, 'Years since last promotion greater than years at the company',
        (SELECT count(*) FROM s WHERE years_since_last_promotion > years_at_company), 'rows', 'kept, flagged'),
    (7, 'Years with current manager greater than years at the company',
        (SELECT count(*) FROM s WHERE years_with_curr_manager > years_at_company), 'rows', 'kept, flagged'),
    (8, 'Years at the company greater than total working years',
        (SELECT count(*) FROM s WHERE years_at_company > total_working_years), 'rows', 'kept, flagged'),
    (9, 'Working years imply starting work before age 14',
        (SELECT count(*) FROM s WHERE total_working_years > age - 14), 'rows', 'kept, flagged'),
    (10, 'Correlation of monthly income with the monthly rate (×100)',
        (SELECT round(100 * corr(monthly_income, monthly_rate)) FROM s), 'r×100',
        'daily, hourly and monthly rates are unrelated to income: excluded from compensation analysis'),
    (11, 'Correlation of monthly income with the hourly rate (×100)',
        (SELECT round(100 * corr(monthly_income, hourly_rate)) FROM s), 'r×100', 'see 10'),
    (12, 'Correlation of monthly income with the daily rate (×100)',
        (SELECT round(100 * corr(monthly_income, daily_rate)) FROM s), 'r×100', 'see 10')
) AS t(id, check_name, value, unit, action);

CREATE OR REPLACE TABLE employees AS
SELECT * EXCLUDE (employee_count, over18, standard_hours, daily_rate, hourly_rate, monthly_rate, business_travel_code),
    (years_in_current_role > years_at_company OR years_since_last_promotion > years_at_company
     OR years_with_curr_manager > years_at_company OR years_at_company > total_working_years
     OR total_working_years > age - 14) AS has_inconsistency
FROM stg_employees;
