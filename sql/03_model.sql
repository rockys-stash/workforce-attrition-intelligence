-- Star model: one fact row per employee, with bands, and small dimensions for the BI layer.
CREATE OR REPLACE TABLE dim_department AS
SELECT row_number() OVER (ORDER BY department) AS department_key, department, count(*) AS employees
FROM employees GROUP BY department;

CREATE OR REPLACE TABLE dim_job_role AS
SELECT row_number() OVER (ORDER BY department, job_role) AS job_role_key, job_role, department, count(*) AS employees
FROM employees GROUP BY department, job_role;

CREATE OR REPLACE TABLE dim_job_level AS
SELECT job_level, count(*) AS employees, median(monthly_income) AS median_income,
       min(monthly_income) AS min_income, max(monthly_income) AS max_income
FROM employees GROUP BY job_level;

CREATE OR REPLACE TABLE fact_employee AS
WITH b AS (
    SELECT e.*,
        ntile(${income_quantiles}) OVER (ORDER BY monthly_income, employee_number) AS income_band,
        monthly_income / l.median_income - 1 AS pay_vs_level_median
    FROM employees e JOIN dim_job_level l USING (job_level)
)
SELECT b.*, d.department_key, r.job_role_key,
    ${tenure_band} AS tenure_band,
    ${age_band} AS age_band,
    ${promotion_band} AS promotion_band,
    CASE WHEN pay_vs_level_median < -${pay_tol} THEN 'Below level median'
         WHEN pay_vs_level_median > ${pay_tol} THEN 'Above level median'
         ELSE 'At level median' END AS pay_position
FROM b JOIN dim_department d USING (department) JOIN dim_job_role r USING (department, job_role);
