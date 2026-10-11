-- Employees and leavers at each completed year of tenure.
SELECT years_at_company AS years, count(*) AS employees, sum(left_company)::INT AS leavers, avg(left_company) AS rate
FROM fact_employee
GROUP BY years_at_company
ORDER BY years_at_company;
