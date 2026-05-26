CREATE DATABASE harsh;
USE harsh;

CREATE TABLE numbers AS
WITH RECURSIVE seq AS (
    SELECT 1 AS n          
    UNION ALL
    SELECT n + 1 FROM seq WHERE n < 100
)
SELECT n FROM seq;

SELECT n 
FROM numbers
LIMIT 5;

WITH RECURSIVE DigitReducer AS (
    SELECT 
        n AS original_num, 
        n AS remaining_num, 
        0 AS digit_sum
    FROM numbers
    UNION ALL
    SELECT
        original_num,
        remaining_num DIV 10,
        digit_sum + (remaining_num % 10)
    FROM DigitReducer
    WHERE remaining_num > 0
)
SELECT n 
FROM numbers n
WHERE NOT EXISTS (
    SELECT 1 
    FROM DigitReducer dr
    WHERE dr.original_num = n.n
      AND dr.remaining_num = 0
      AND (dr.digit_sum = 0 OR n.n % dr.digit_sum <> 0)
);
