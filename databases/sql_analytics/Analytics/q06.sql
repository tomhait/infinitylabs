USE oulad_db;

SELECT 
    assessment_type,
    code_module,
    (AVG(x * y) - AVG(x) * AVG(y)) / (STDDEV(x) * STDDEV(y)) AS correlation_coefficient
FROM (
    WITH assessment_averages AS (
        SELECT 
            sa.id_student, 
            a.code_module, 
            a.code_presentation, 
            a.assessment_type,
            AVG(sa.score) as avg_assessment_score
        FROM student_assessment sa
        JOIN assessments a ON sa.id_assessment = a.id_assessment
        WHERE a.assessment_type IN ('TMA', 'CMA')
        GROUP BY sa.id_student, a.code_module, a.code_presentation, a.assessment_type
    ),
    exam_scores AS (
        SELECT 
            sa.id_student, 
            a.code_module, 
            a.code_presentation, 
            sa.score as exam_score
        FROM student_assessment sa
        JOIN assessments a ON sa.id_assessment = a.id_assessment
        WHERE a.assessment_type = 'Exam'
    )
    SELECT 
        ea.assessment_type,
        ea.code_module,
        ea.avg_assessment_score AS X,
        es.exam_score AS Y
    FROM assessment_averages ea
    JOIN exam_scores es ON ea.id_student = es.id_student 
        AND ea.code_module = es.code_module 
        AND ea.code_presentation = es.code_presentation
) AS correlation_data
GROUP BY assessment_type, code_module;

assessment_type|code_module|correlation_coefficient|
---------------+-----------+-----------------------+
CMA            |CCC        |     0.7411346010044767|
TMA            |CCC        |     0.7167525210696842|
CMA            |DDD        |     0.6623510775429419|
TMA            |DDD        |     0.6251828033733712|
