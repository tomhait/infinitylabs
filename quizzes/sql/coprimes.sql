CREATE DATABASE primes;
USE primes;

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

SELECT a,b FROM numbers(n)
WHERE a>b AND NOT EXISTS (
	SELECT r FROM numbers(n)
	WHERE r>1 AND a%r=0 AND b%r=0
);