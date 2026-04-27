USE oulad_db;

SELECT
	s1.code_presentation as semester,
    s1.code_module AS module_a, 
    s2.code_module AS module_b, 
    COUNT(DISTINCT s1.id_student) AS student_count
FROM student_info s1
JOIN student_info s2 ON s1.id_student = s2.id_student
AND s1.code_presentation = s2.code_presentation
AND s1.code_module < s2.code_module
GROUP BY semester, module_a, module_b
ORDER BY student_count DESC
LIMIT 20;

semester|module_a|module_b|student_count|
--------+--------+--------+-------------+
2014B   |CCC     |EEE     |          311|
2014J   |CCC     |EEE     |          287|
2014J   |CCC     |DDD     |          151|
2014J   |CCC     |FFF     |          134|
2014B   |CCC     |FFF     |           77|
2014B   |CCC     |DDD     |           72|
2013J   |DDD     |FFF     |            8|
2014J   |DDD     |FFF     |            6|
2014B   |DDD     |FFF     |            5|
2014J   |EEE     |FFF     |            5|
2013J   |DDD     |EEE     |            4|
2014J   |BBB     |DDD     |            4|
2014J   |DDD     |EEE     |            3|
2014B   |BBB     |GGG     |            3|
2013B   |BBB     |DDD     |            3|
2014B   |DDD     |EEE     |            2|
2013J   |EEE     |FFF     |            2|
2013B   |BBB     |FFF     |            2|
2014B   |FFF     |GGG     |            1|
2014B   |EEE     |FFF     |            1|