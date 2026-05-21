USE oulad_db;

SELECT 
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

age_band|avg_clicks_per_student|
--------+----------------------+
0-35    |               1445.89|
35-55   |               2001.85|
55<=    |               3271.58|
