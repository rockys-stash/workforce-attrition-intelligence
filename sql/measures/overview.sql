SELECT count(*) AS employees, sum(left_company)::INT AS leavers, avg(left_company) AS rate,
       median(monthly_income) AS median_income, avg(overtime) AS overtime_share,
       median(years_at_company) AS median_tenure, median(age) AS median_age,
       sum(has_inconsistency::INT)::INT AS inconsistent_rows
FROM fact_employee;
