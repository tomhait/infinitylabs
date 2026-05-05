CREATE DATABASE coprimes;
USE coprimes;

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

SELECT a.n,
	   b.n
FROM numbers a
JOIN numbers b ON a.n > b.n
WHERE NOT EXISTS (
	SELECT 1 FROM numbers r
	WHERE r.n>1 AND a.n%r.n=0 AND b.n%r.n=0
);