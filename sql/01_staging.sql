-- Raw CSV to typed, snake_case columns. Nothing is dropped here.
CREATE OR REPLACE TABLE raw_employees AS
SELECT * FROM read_csv('${source}', header = true, auto_detect = true);

CREATE OR REPLACE TABLE stg_employees AS
SELECT
    CAST(EmployeeNumber AS INTEGER)            AS employee_number,
    CAST(Attrition = 'Yes' AS INTEGER)          AS left_company,
    CAST(Age AS INTEGER)                        AS age,
    CAST(Gender AS VARCHAR)                     AS gender,
    CAST(MaritalStatus AS VARCHAR)              AS marital_status,
    CAST(Department AS VARCHAR)                 AS department,
    CAST(JobRole AS VARCHAR)                    AS job_role,
    CAST(JobLevel AS INTEGER)                   AS job_level,
    CAST(BusinessTravel AS VARCHAR)             AS business_travel_code,
    CASE BusinessTravel WHEN 'Non-Travel' THEN 'None' WHEN 'Travel_Rarely' THEN 'Rarely'
                        WHEN 'Travel_Frequently' THEN 'Frequently' END AS business_travel,
    CAST(OverTime = 'Yes' AS INTEGER)           AS overtime,
    CAST(MonthlyIncome AS DOUBLE)               AS monthly_income,
    CAST(PercentSalaryHike AS INTEGER)          AS percent_salary_hike,
    CAST(StockOptionLevel AS INTEGER)           AS stock_option_level,
    CAST(DailyRate AS DOUBLE)                   AS daily_rate,
    CAST(HourlyRate AS DOUBLE)                  AS hourly_rate,
    CAST(MonthlyRate AS DOUBLE)                 AS monthly_rate,
    CAST(YearsAtCompany AS INTEGER)             AS years_at_company,
    CAST(YearsInCurrentRole AS INTEGER)         AS years_in_current_role,
    CAST(YearsSinceLastPromotion AS INTEGER)    AS years_since_last_promotion,
    CAST(YearsWithCurrManager AS INTEGER)       AS years_with_curr_manager,
    CAST(TotalWorkingYears AS INTEGER)          AS total_working_years,
    CAST(NumCompaniesWorked AS INTEGER)         AS num_companies_worked,
    CAST(TrainingTimesLastYear AS INTEGER)      AS training_times_last_year,
    CAST(DistanceFromHome AS INTEGER)           AS distance_from_home,
    CAST(Education AS INTEGER)                  AS education,
    CAST(EducationField AS VARCHAR)             AS education_field,
    CAST(PerformanceRating AS INTEGER)          AS performance_rating,
    CAST(JobSatisfaction AS INTEGER)            AS job_satisfaction,
    CAST(EnvironmentSatisfaction AS INTEGER)    AS environment_satisfaction,
    CAST(RelationshipSatisfaction AS INTEGER)   AS relationship_satisfaction,
    CAST(JobInvolvement AS INTEGER)             AS job_involvement,
    CAST(WorkLifeBalance AS INTEGER)            AS work_life_balance,
    CAST(EmployeeCount AS INTEGER)              AS employee_count,
    CAST(Over18 AS VARCHAR)                     AS over18,
    CAST(StandardHours AS INTEGER)              AS standard_hours
FROM raw_employees;
