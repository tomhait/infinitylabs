USE oulad_db;

SELECT 
    CASE 
        WHEN date_unregistration < 0 THEN 'Before Start'
        WHEN date_unregistration BETWEEN 0 AND 30 THEN 'Month 1'
        WHEN date_unregistration BETWEEN 31 AND 90 THEN 'Months 2-3'
        WHEN date_unregistration > 90 THEN 'After month 3'
        ELSE 'Finished Course'
    END AS cancellation_window,
    COUNT(*) AS student_count
FROM student_registration
GROUP BY cancellation_window;

cancellation_window|student_count|
-------------------+-------------+
Finished Course    |        22521|
Month 1            |         2449|
After month 3      |         3041|
Months 2-3         |         1904|
Before Start       |         2678|