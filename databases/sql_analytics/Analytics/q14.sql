USE oulad_db;

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
	
activity_type |distinction_count|pass_count|fail_count|avg_clicks_distinction|avg_clicks_pass|avg_clicks_fail|
--------------+-----------------+----------+----------+----------------------+---------------+---------------+
repeatactivity|                0|         1|         1|                      |           1.00|           1.00|
sharedsubpage |               17|        68|        28|                  1.05|           1.11|           1.14|
folder        |              307|      1475|       223|                  1.12|           1.16|           1.24|
externalquiz  |              417|      2193|      1205|                  1.19|           1.26|           1.31|
page          |             1231|      4189|      1906|                  1.28|           1.31|           1.41|
resource      |             2899|     11858|      6005|                  1.31|           1.38|           1.37|
htmlactivity  |              266|       844|       334|                  1.36|           1.36|           1.31|
questionnaire |              791|      2724|       649|                  1.39|           1.45|           1.54|
url           |             2453|     10436|      5112|                  1.41|           1.39|           1.38|
oucollaborate |             1551|      5706|      1943|                  1.61|           1.67|           1.70|
subpage       |             2902|     11862|      6211|                  1.73|           1.73|           1.77|
ouelluminate  |              234|      1304|       667|                  1.74|           1.80|           1.63|
dualpane      |              707|      2260|       622|                  2.01|           2.03|           2.28|
forumng       |             2851|     11525|      5553|                  3.45|           3.25|           3.16|
dataplus      |              608|      1953|       158|                  3.66|           3.47|           3.48|
homepage      |             2903|     11877|      6469|                  4.38|           3.92|           3.70|
glossary      |              938|      3428|      1062|                  5.63|           5.08|           4.22|
ouwiki        |             1345|      5716|      2283|                  5.73|           5.12|           4.58|
oucontent     |             2844|     11528|      5803|                  5.86|           5.75|           5.39|
quiz          |             2558|      9424|      4135|                  7.23|           7.82|           8.01|
