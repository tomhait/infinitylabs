CREATE DATABASE primes;
USE primes;

CREATE TABLE numbers AS
WITH RECURSIVE seq AS (
    SELECT 1 AS n          
    UNION ALL
    SELECT n + 1 FROM seq WHERE n < 100
)
SELECT n FROM seq
UNION ALL
SELECT n FROM seq;

SELECT n 
FROM numbers
LIMIT 5;

WITH coef AS (
    SELECT SQRT(MAX(n)) AS up_to FROM numbers
)
SELECT 
    DISTINCT n
FROM numbers 
WHERE n > 1 AND NOT EXISTS (
    SELECT 1 
    FROM (SELECT DISTINCT n FROM numbers) AS k, coef
    WHERE k.n > 1 
      AND k.n <= coef.up_to 
      AND numbers.n % k.n = 0
      AND numbers.n <> k.n
);

DROP TABLE numbers;