SELECT income_band, min(monthly_income) AS min_income, max(monthly_income) AS max_income, count(*) AS employees,
       sum(left_company)::INT AS leavers, avg(left_company) AS rate
FROM fact_employee
GROUP BY income_band
ORDER BY income_band;
