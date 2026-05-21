USE oulad_db;

# do multiple course attempts lead to success?
SELECT 
    num_of_prev_attempts,
    COUNT(*) AS student_count,
    ROUND(100 * SUM(CASE WHEN final_result IN ('Pass', 'Distinction') THEN 1 ELSE 0 END) / COUNT(*), 2) AS success_rate_pct,
    ROUND(100 * SUM(CASE WHEN final_result = 'Distinction' THEN 1 ELSE 0 END) / COUNT(*), 2) AS distinction_rate_pct
FROM student_info
GROUP BY num_of_prev_attempts
ORDER BY num_of_prev_attempts ASC;

num_of_prev_attempts|student_count|success_rate_pct|distinction_rate_pct|
--------------------+-------------+----------------+--------------------+
                   0|        28421|           49.28|               10.05|
                   1|         3299|           34.56|                4.33|
                   2|          675|           28.44|                3.26|
                   3|          142|           22.54|                0.70|
                   4|           39|           33.33|                0.00|
                   5|           13|           15.38|                0.00|
                   6|            4|           25.00|               25.00|
                   
# does the geographic region of the student affect on its succerss?
SELECT 
    region,
    COUNT(*) AS total_students,
    ROUND(100 * SUM(CASE WHEN final_result IN ('Pass', 'Distinction') THEN 1 ELSE 0 END) / COUNT(*), 2) AS success_rate_pct,
    ROUND(100 * SUM(CASE WHEN final_result = 'Distinction' THEN 1 ELSE 0 END) / COUNT(*), 2) AS distinction_rate_pct,
    ROUND(100 * SUM(CASE WHEN final_result = 'Withdrawn' THEN 1 ELSE 0 END) / COUNT(*), 2) AS withdrawal_rate_pct
FROM student_info
GROUP BY region
ORDER BY success_rate_pct DESC;

region              |total_students|success_rate_pct|distinction_rate_pct|withdrawal_rate_pct|
--------------------+--------------+----------------+--------------------+-------------------+
Ireland             |          1184|           54.90|                8.28|              23.06|
South Region        |          3092|           52.39|               10.77|              30.01|
South East Region   |          2111|           51.49|               11.56|              30.74|
North Region        |          1823|           50.52|               12.62|              31.54|
South West Region   |          2436|           49.79|               10.84|              31.12|
East Anglian Region |          3340|           48.98|                9.79|              30.12|
Scotland            |          3446|           48.96|                9.52|              26.32|
East Midlands Region|          2365|           45.71|                8.46|              34.76|
Wales               |          2086|           45.16|                8.49|              25.12|
Yorkshire Region    |          2006|           44.87|                8.23|              32.75|
West Midlands Region|          2582|           43.30|                7.05|              35.36|
London Region       |          3216|           42.35|                8.18|              34.51|
North Western Region|          2906|           40.19|                7.33|              35.58|

# do students who submit their exercies earlier tend to succeed?
SELECT 
    CASE 
        WHEN (a.date - sa.date_submitted) >= 10 THEN '1. Very Early (10+ days)'
        WHEN (a.date - sa.date_submitted) BETWEEN 1 AND 9 THEN '2. Slightly Early'
        WHEN (a.date - sa.date_submitted) = 0 THEN '3. On the Deadline'
        ELSE '4. Late Submission'
    END AS days_to_submission,
    COUNT(DISTINCT si.id_student) AS student_count,
    ROUND(100 * SUM(CASE WHEN si.final_result IN ('Pass', 'Distinction') THEN 1 ELSE 0 END) / COUNT(*), 2) AS success_rate_pct,
    ROUND(100 * SUM(CASE WHEN si.final_result = 'Distinction' THEN 1 ELSE 0 END) / COUNT(*), 2) AS distinction_rate_pct
FROM student_assessment sa
JOIN assessments a ON sa.id_assessment = a.id_assessment
JOIN student_info si ON sa.id_student = si.id_student
WHERE a.assessment_type != 'Exam'
GROUP BY days_to_submission
ORDER BY days_to_submission;

days_to_submission      |student_count|success_rate_pct|distinction_rate_pct|
------------------------+-------------+----------------+--------------------+
1. Very Early (10+ days)|         8211|           76.72|               18.53|
2. Slightly Early       |        17490|           76.58|               16.91|
3. On the Deadline      |        12983|           65.34|                9.66|
4. Late Submission      |        14390|           65.36|               12.15|

# do students from low income areas tend to less succeed?
SELECT 
    imd_band,
    COUNT(*) AS student_count,
    ROUND(100 * SUM(CASE WHEN final_result IN ('Pass', 'Distinction') THEN 1 ELSE 0 END) / COUNT(*), 2) AS success_rate_pct,
    ROUND(100 * SUM(CASE WHEN final_result = 'Fail' THEN 1 ELSE 0 END) / COUNT(*), 2) AS fail_rate_pct,
    ROUND(100 * SUM(CASE WHEN final_result = 'Withdrawn' THEN 1 ELSE 0 END) / COUNT(*), 2) AS withdrawal_rate_pct
FROM student_info WHERE imd_band <> ''
GROUP BY imd_band
ORDER BY imd_band ASC;

imd_band|student_count|success_rate_pct|fail_rate_pct|withdrawal_rate_pct|
--------+-------------+----------------+-------------+-------------------+
0-10%   |         3311|           35.16|        27.67|              37.18|
10-20   |         3516|           38.62|        25.94|              35.44|
20-30%  |         3654|           40.75|        23.10|              36.15|
30-40%  |         3539|           46.91|        22.15|              30.94|
40-50%  |         3256|           46.59|        21.41|              32.00|
50-60%  |         3124|           48.78|        22.44|              28.78|
60-70%  |         2905|           51.91|        18.52|              29.57|
70-80%  |         2879|           51.51|        20.81|              27.68|
80-90%  |         2762|           54.06|        17.92|              28.02|
90-100% |         2536|           57.53|        16.60|              25.87|

# do studtens who repeated a course succeded more when doing again the assignments?
SELECT 
    CASE 
        WHEN sa.is_banked = 1 THEN 'Transferred Credits'
        ELSE 'Redid All Assignments'
    END AS repeater_strategy,
    COUNT(DISTINCT si.id_student) AS student_count,
    ROUND(100 * SUM(CASE WHEN si.final_result IN ('Pass', 'Distinction') THEN 1 ELSE 0 END) / COUNT(*), 2) AS success_rate_pct,
    ROUND(AVG(sa.score), 2) AS avg_assessment_score
FROM student_info si
JOIN student_assessment sa ON si.id_student = sa.id_student 
JOIN assessments s ON si.code_module = s.code_module
AND s.id_assessment = sa.id_assessment
WHERE si.num_of_prev_attempts > 0
GROUP BY repeater_strategy;

repeater_strategy    |student_count|success_rate_pct|avg_assessment_score|
---------------------+-------------+----------------+--------------------+
Redid All Assignments|         3066|           58.81|               71.09|
Transferred Credits  |          523|           29.86|               74.33|
