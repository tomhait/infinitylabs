USE oulad_db;

WITH ranked_scores AS (
    SELECT 
        sa.id_student,
        a.code_module,
        a.code_presentation,
        sa.score,
        RANK() OVER (    
        	PARTITION BY sa.id_student, a.code_module, a.code_presentation 
            ORDER BY sa.date_submitted ASC
        ) as submission_order,
        COUNT(*) OVER (
            PARTITION BY sa.id_student, a.code_module, a.code_presentation
        ) as total_submissions
    FROM student_assessment sa
    JOIN assessments a ON sa.id_assessment = a.id_assessment
    WHERE a.assessment_type != 'Exam'
)
SELECT 
    code_module,
    code_presentation,
    AVG(CASE WHEN submission_order = 1 THEN score END) as initial_avg_score,
    AVG(CASE WHEN submission_order = total_submissions AND total_submissions > 1 THEN score END) as final_avg_score,
    AVG(CASE WHEN submission_order = total_submissions AND total_submissions > 1 THEN score END) - 
    AVG(CASE WHEN submission_order = 1 THEN score END) as avg_improvement
FROM ranked_scores
GROUP BY code_module, code_presentation
ORDER BY avg_improvement DESC;

code_module|code_presentation|initial_avg_score|final_avg_score|avg_improvement|
-----------+-----------------+-----------------+---------------+---------------+
GGG        |2013J            |          67.9344|        83.9186|        15.9842|
GGG        |2014J            |          66.9855|        81.9600|        14.9745|
GGG        |2014B            |          69.2489|        82.6288|        13.3799|
BBB        |2013B            |          71.4582|        81.2450|         9.7868|
BBB        |2013J            |          72.5135|        82.1634|         9.6499|
BBB        |2014B            |          71.8947|        81.4734|         9.5787|
BBB        |2014J            |          58.8661|        67.4285|         8.5624|
CCC        |2014B            |          60.4703|        64.4298|         3.9595|
AAA        |2014J            |          69.1319|        67.6218|        -1.5101|
AAA        |2013J            |          69.9588|        67.5436|        -2.4152|
FFF        |2014J            |          78.8440|        72.7183|        -6.1257|
CCC        |2014J            |          73.8795|        67.6218|        -6.2578|
EEE        |2013J            |          83.6208|        76.2417|        -7.3791|
EEE        |2014J            |          85.9853|        78.2933|        -7.6921|
DDD        |2013B            |          68.2045|        60.1789|        -8.0255|
FFF        |2013J            |          78.4561|        70.2212|        -8.2349|
DDD        |2014J            |          72.4275|        63.2261|        -9.2014|
FFF        |2014B            |          79.8126|        69.7329|       -10.0797|
FFF        |2013B            |          80.6401|        70.3629|       -10.2772|
EEE        |2014B            |          85.6045|        72.8624|       -12.7421|
DDD        |2014B            |          70.7789|        57.6714|       -13.1075|
DDD        |2013J            |          72.3152|        58.6080|       -13.7072|