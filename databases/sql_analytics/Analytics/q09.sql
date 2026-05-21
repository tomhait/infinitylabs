USE oulad_db;

SELECT 
    si.code_module,
    si.code_presentation,
    ROUND(AVG(sa.score), 2) AS avg_score,
    ROUND(100 * COUNT(DISTINCT CASE WHEN si.final_result = 'Fail' THEN si.id_student END) 
          / COUNT(DISTINCT si.id_student), 2) AS fail_rate_pct,
    COUNT(DISTINCT si.id_student) AS student_count
FROM student_info si
LEFT JOIN student_assessment sa ON si.id_student = sa.id_student
GROUP BY si.code_module, si.code_presentation
ORDER BY si.code_module, si.code_presentation;

code_module|code_presentation|avg_score|fail_rate_pct|student_count|
-----------+-----------------+---------+-------------+-------------+
AAA        |2013J            |    69.51|        11.75|          383|
AAA        |2014J            |    68.76|        12.60|          365|
BBB        |2013B            |    78.84|        25.98|         1767|
BBB        |2013J            |    78.69|        23.29|         2237|
BBB        |2014B            |    78.61|        24.55|         1613|
BBB        |2014J            |    66.94|        17.06|         2292|
CCC        |2014B            |    73.20|        19.37|         1936|
CCC        |2014J            |    75.96|        16.25|         2498|
DDD        |2013B            |    69.50|        27.71|         1303|
DDD        |2013J            |    69.91|        22.08|         1938|
DDD        |2014B            |    69.19|        21.09|         1228|
DDD        |2014J            |    71.49|        20.19|         1803|
EEE        |2013J            |    75.08|        19.01|         1052|
EEE        |2014B            |    73.99|        23.63|          694|
EEE        |2014J            |    79.58|        16.67|         1188|
FFF        |2013B            |    77.50|        26.08|         1614|
FFF        |2013J            |    76.69|        22.47|         2283|
FFF        |2014B            |    76.16|        25.60|         1500|
FFF        |2014J            |    78.19|        16.62|         2365|
GGG        |2013J            |    79.93|        30.88|          952|
GGG        |2014B            |    79.50|        30.61|          833|
GGG        |2014J            |    79.09|        23.90|          749|