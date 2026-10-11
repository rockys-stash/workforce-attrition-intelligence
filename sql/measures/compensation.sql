-- Pay by job level, for stayers and leavers.
SELECT job_level, count(*) AS employees, sum(left_company)::INT AS leavers, avg(left_company) AS rate,
       median(monthly_income) AS median_income,
       median(monthly_income) FILTER (WHERE left_company = 0) AS median_income_stayed,
       median(monthly_income) FILTER (WHERE left_company = 1) AS median_income_left,
       avg(overtime) AS overtime_share, avg((stock_option_level = 0)::INT) AS no_stock_share
FROM fact_employee
GROUP BY job_level
ORDER BY job_level;
