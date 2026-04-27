USE oulad_db;

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

study_period |final_result|student_count|avg_click_work|
-------------+------------+-------------+--------------+
Before course|Distinction |         2598|          3.53|
Before course|Pass        |        10046|          3.15|
Before course|Fail        |         4726|          2.90|
Before course|Withdrawn   |         5331|          2.86|
Exam Prep    |Fail        |         3224|          4.11|
Exam Prep    |Pass        |        11864|          4.02|
Exam Prep    |Distinction |         2903|          3.97|
Exam Prep    |Withdrawn   |          952|          3.41|
Months 1-2   |Distinction |         2895|          3.93|
Months 1-2   |Pass        |        11830|          3.66|
Months 1-2   |Withdrawn   |         5983|          3.45|
Months 1-2   |Fail        |         6302|          3.43|
Months 3-5   |Distinction |         2899|          3.88|
Months 3-5   |Pass        |        11861|          3.70|
Months 3-5   |Fail        |         4836|          3.45|
Months 3-5   |Withdrawn   |         3024|          3.31|