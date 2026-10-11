-- Attrition by one factor. ${factor} is a column name from a fixed list in wfintel.db.FACTORS.
SELECT ${factor} AS level, count(*) AS employees, sum(left_company)::INT AS leavers, avg(left_company) AS rate
FROM fact_employee
GROUP BY 1
ORDER BY 1;
