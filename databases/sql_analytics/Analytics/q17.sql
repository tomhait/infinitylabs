USE oulad_db;

# execution time - run SHOW PROFILES at the end
SET profiling = 1;

SHOW INDEX IN student_vle;

CREATE INDEX idx_vle_module ON student_vle(code_module, code_presentation, id_student);

# q13
EXPLAIN SELECT 
    si.age_band,
    ROUND(AVG(total_clicks), 2) AS avg_clicks_per_student
FROM student_info si
JOIN (
    SELECT id_student, SUM(sum_click) AS total_clicks
    FROM student_vle
    GROUP BY id_student
) AS clicks ON si.id_student = clicks.id_student
GROUP BY si.age_band
ORDER BY avg_clicks_per_student ASC;

EXPLAIN SELECT 
    si.age_band,
    ROUND(AVG(total_clicks), 2) AS avg_clicks_per_student
FROM student_info si
JOIN (
    SELECT id_student, SUM(sum_click) AS total_clicks
    FROM student_vle IGNORE INDEX (id_student)
    GROUP BY id_student
) AS clicks ON si.id_student = clicks.id_student
GROUP BY si.age_band
ORDER BY avg_clicks_per_student ASC;

# q14
SELECT 
    v.activity_type,
    COUNT(DISTINCT CASE WHEN si.final_result = 'Distinction' THEN si.id_student END) AS distinction_count,
    COUNT(DISTINCT CASE WHEN si.final_result = 'Pass' THEN si.id_student END) AS pass_count,
    COUNT(DISTINCT CASE WHEN si.final_result = 'Fail' THEN si.id_student END) AS fail_count,
    ROUND(AVG(CASE WHEN si.final_result = 'Distinction' THEN sv.sum_click END), 2) AS avg_clicks_distinction,
    ROUND(AVG(CASE WHEN si.final_result = 'Pass' THEN sv.sum_click END), 2) AS avg_clicks_pass,
    ROUND(AVG(CASE WHEN si.final_result = 'Fail' THEN sv.sum_click END), 2) AS avg_clicks_fail
FROM student_vle sv
JOIN vle v ON sv.id_site = v.id_site
JOIN student_info si ON sv.id_student = si.id_student
GROUP BY v.activity_type
ORDER BY avg_clicks_distinction ASC;

SELECT 
    v.activity_type,
    COUNT(DISTINCT CASE WHEN si.final_result = 'Distinction' THEN si.id_student END) AS distinction_count,
    COUNT(DISTINCT CASE WHEN si.final_result = 'Pass' THEN si.id_student END) AS pass_count,
    COUNT(DISTINCT CASE WHEN si.final_result = 'Fail' THEN si.id_student END) AS fail_count,
    ROUND(AVG(CASE WHEN si.final_result = 'Distinction' THEN sv.sum_click END), 2) AS avg_clicks_distinction,
    ROUND(AVG(CASE WHEN si.final_result = 'Pass' THEN sv.sum_click END), 2) AS avg_clicks_pass,
    ROUND(AVG(CASE WHEN si.final_result = 'Fail' THEN sv.sum_click END), 2) AS avg_clicks_fail
FROM student_vle sv IGNORE INDEX (id_student)
JOIN vle v ON sv.id_site = v.id_site
JOIN student_info si ON sv.id_student = si.id_student
GROUP BY v.activity_type
ORDER BY avg_clicks_distinction ASC;

# q15
SELECT 
    CASE 
        WHEN sv.date < 0 THEN 'Before course'
        WHEN sv.date BETWEEN 0 AND 60 THEN 'Months 1-2'
        WHEN sv.date BETWEEN 61 AND 150 THEN 'Months 3-5'
        ELSE 'Exam Prep'
    END AS study_period,
    si.final_result,
    COUNT(DISTINCT si.id_student) AS student_count,
    ROUND(AVG(sv.sum_click), 2) AS avg_click_work
FROM student_vle sv
JOIN student_info si ON sv.id_student = si.id_student 
    AND sv.code_module = si.code_module 
    AND sv.code_presentation = si.code_presentation
GROUP BY study_period, si.final_result
ORDER BY study_period, avg_click_work DESC;

SELECT 
    CASE 
        WHEN sv.date < 0 THEN 'Before course'
        WHEN sv.date BETWEEN 0 AND 60 THEN 'Months 1-2'
        WHEN sv.date BETWEEN 61 AND 150 THEN 'Months 3-5'
        ELSE 'Exam Prep'
    END AS study_period,
    si.final_result,
    COUNT(DISTINCT si.id_student) AS student_count,
    ROUND(AVG(sv.sum_click), 2) AS avg_click_work
FROM student_vle sv IGNORE INDEX (id_student)
JOIN student_info si ON sv.id_student = si.id_student 
    AND sv.code_module = si.code_module 
    AND sv.code_presentation = si.code_presentation
GROUP BY study_period, si.final_result
ORDER BY study_period, avg_click_work DESC;

# show index size
SELECT 
    table_name AS `Table`, 
    ROUND(((data_length) / 1024 / 1024), 2) AS `Data (MB)`, 
    ROUND(((index_length) / 1024 / 1024), 2) AS `Index (MB)`,
    ROUND(((data_length + index_length) / 1024 / 1024), 2) AS `Total Size (MB)`
FROM information_schema.TABLES 
WHERE table_schema = 'oulad_db'
ORDER BY (data_length + index_length) DESC;



SHOW PROFILES;
