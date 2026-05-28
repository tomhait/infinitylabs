import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore")
from pyspark.sql import SparkSession
import pyspark.sql.functions as F


n = 100

spark = SparkSession.builder.master("spark://spark-master:7077")\
    .appName("CoPrimes").getOrCreate()

numbers = spark.range(1, n+1).withColumnRenamed("id", "n")
numbers.show(5)

divisors_df = numbers.withColumn(
    "divisors",
    F.expr("filter(sequence(2, n), x -> (n % x == 0))")
)

a = divisors_df.alias("a")
b = divisors_df.alias("b")

coprime_pairs = a.join(b, F.col("a.n") > F.col("b.n"), how="inner") \
    .withColumn("common_divisors", F.array_intersect(F.col("a.divisors"), F.col("b.divisors"))) \
    .filter(F.size(F.col("common_divisors")) == 0) \
    .select(
        F.col("a.n").alias("a.n"),
        F.col("b.n").alias("b.n")
    )

print(f"\nList of coprimes up to n={n}:")
coprime_pairs.show(n = n)