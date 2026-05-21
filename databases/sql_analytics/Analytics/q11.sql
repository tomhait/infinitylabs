USE oulad_db;

SELECT 
    a.weight,
    COUNT(DISTINCT a.id_assessment) AS number_of_assessments,
    ROUND(AVG(sa.score), 2) AS avg_score
FROM assessments a
JOIN student_assessment sa ON a.id_assessment = sa.id_assessment
WHERE a.assessment_type != 'Exam' AND a.weight > 0
GROUP BY a.weight
ORDER BY a.weight ASC;

weight|number_of_assessments|avg_score|
------+---------------------+---------+
  1.00|                   15|    88.05|
  2.00|                    3|    68.33|
  3.00|                    3|    74.26|
  4.00|                    2|    73.38|
  5.00|                    4|    71.68|
  6.00|                    1|    63.64|
  7.00|                    2|    78.10|
  7.50|                    1|    71.07|
  8.00|                    4|    73.45|
  9.00|                    2|    77.10|
 10.00|                    8|    72.75|
 12.50|                   11|    76.50|
 15.00|                    3|    64.29|
 16.00|                    3|    85.16|
 17.50|                    2|    76.87|
 18.00|                   15|    71.66|
 20.00|                   13|    65.64|
 22.00|                    6|    73.36|
 25.00|                   15|    72.58|
 28.00|                    9|    79.56|
 30.00|                    2|    69.17|
 35.00|                    2|    68.31|