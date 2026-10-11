SELECT 'fact_employee' AS table_name, count(*) AS rows FROM fact_employee
UNION ALL SELECT 'dim_department', count(*) FROM dim_department
UNION ALL SELECT 'dim_job_role', count(*) FROM dim_job_role
UNION ALL SELECT 'dim_job_level', count(*) FROM dim_job_level;
