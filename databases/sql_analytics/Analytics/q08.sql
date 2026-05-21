USE oulad_db;

# education level
SELECT 
    highest_education,
    COUNT(id_student) AS total_students,
    ROUND(100 * SUM(CASE WHEN final_result IN ('Pass', 'Distinction') THEN 1 ELSE 0 END) / COUNT(*), 2) AS success_rate_pct,
    ROUND(100 * SUM(CASE WHEN final_result = 'Distinction' THEN 1 ELSE 0 END) / COUNT(*), 2) AS distinction_rate_pct,
    ROUND(100 * SUM(CASE WHEN final_result = 'Withdrawn' THEN 1 ELSE 0 END) / COUNT(*), 2) AS withdrawal_rate_pct
FROM student_info
GROUP BY highest_education
ORDER BY success_rate_pct DESC;

highest_education          |total_students|success_rate_pct|distinction_rate_pct|withdrawal_rate_pct|
---------------------------+--------------+----------------+--------------------+-------------------+
Post Graduate Qualification|           313|           65.50|               28.12|              23.64|
HE Qualification           |          4730|           56.17|               14.74|              27.12|
A Level or Equivalent      |         14045|           52.03|               10.65|              28.69|
Lower Than A Level         |         13158|           38.85|                5.53|              35.11|
No Formal quals            |           347|           29.68|                4.61|              42.94|

# gender
SELECT 
    gender,
    COUNT(id_student) AS total_students,
    ROUND(100 * SUM(CASE WHEN final_result IN ('Pass', 'Distinction') THEN 1 ELSE 0 END) / COUNT(*), 2) AS success_rate_pct,
    ROUND(100 * SUM(CASE WHEN final_result = 'Distinction' THEN 1 ELSE 0 END) / COUNT(*), 2) AS distinction_rate_pct,
    ROUND(100 * SUM(CASE WHEN final_result = 'Withdrawn' THEN 1 ELSE 0 END) / COUNT(*), 2) AS withdrawal_rate_pct
FROM student_info
GROUP BY gender
ORDER BY success_rate_pct DESC;

gender|total_students|success_rate_pct|distinction_rate_pct|withdrawal_rate_pct|
------+--------------+----------------+--------------------+-------------------+
F     |         14718|           48.44|                9.47|              30.48|
M     |         17875|           46.19|                9.12|              31.72|

# disability
SELECT 
    disability,
    COUNT(id_student) AS total_students,
    ROUND(100 * SUM(CASE WHEN final_result IN ('Pass', 'Distinction') THEN 1 ELSE 0 END) / COUNT(*), 2) AS success_rate_pct,
    ROUND(100 * SUM(CASE WHEN final_result = 'Distinction' THEN 1 ELSE 0 END) / COUNT(*), 2) AS distinction_rate_pct,
    ROUND(100 * SUM(CASE WHEN final_result = 'Withdrawn' THEN 1 ELSE 0 END) / COUNT(*), 2) AS withdrawal_rate_pct
FROM student_info
GROUP BY disability
ORDER BY success_rate_pct DESC;

disability|total_students|success_rate_pct|distinction_rate_pct|withdrawal_rate_
----------+--------------+----------------+--------------------+----------------
N         |         29429|           48.18|                9.52|              30
Y         |          3164|           38.15|                7.05|              39

