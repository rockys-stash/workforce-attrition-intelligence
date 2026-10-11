-- Department and role profile: size, attrition, pay, overtime, satisfaction, tenure.
SELECT department, job_role, count(*) AS employees, sum(left_company)::INT AS leavers, avg(left_company) AS rate,
       median(monthly_income) AS median_income, avg(overtime) AS overtime_share,
       avg(job_satisfaction) AS mean_job_satisfaction, median(years_at_company) AS median_tenure,
       avg(job_level) AS mean_job_level
FROM fact_employee
GROUP BY ALL
ORDER BY department, employees DESC;
