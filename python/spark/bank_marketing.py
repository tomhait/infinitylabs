import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", category=FutureWarning)
from pyspark.sql import SparkSession
import pyspark.sql.functions as F
import pyspark.sql.types as T
from pathlib import Path
import matplotlib.pyplot as plt
import seaborn as sns


folder = Path("/opt/spark/apps")
file_path = folder / "bank.csv"

spark = SparkSession.builder.master("spark://spark-master:7077") \
    .appName("Bank-Marketing").getOrCreate()

print("Spark session created!")

df = spark.read.csv(str(file_path), header=True, inferSchema=True)

print("\nOriginal DataFrame Schema:")
df.printSchema()

print("\nOriginal Data Table:")
df.show()

print("\n10 random rows from the Table:")
df.orderBy(F.rand(seed=42)).limit(10).show()

total_count = df.count()

print("\nRelative Proportions for 'deposit':")
df.groupBy("deposit") \
  .count() \
  .withColumn("proportion", F.round(F.col("count") / total_count, 2)) \
  .show()

if "education" in df.columns:
    print("\nRelative Proportions for 'education':")
    df.groupBy("education") \
      .count() \
      .withColumn("proportion", F.round(F.col("count") / total_count, 2)) \
      .show()

numerical_cols = [
    field.name for field in df.schema.fields
    if isinstance(field.dataType, (T.IntegerType, T.DoubleType, T.LongType, T.FloatType, T.ShortType))
]
print("\nDescriptive Statistics for Numerical Variables:")
df.select(numerical_cols).summary().show()


# visualizations
pd_deposit = df.groupBy("deposit").count().toPandas()

plt.figure(figsize=(6, 4))
sns.barplot(x="deposit", y="count", data=pd_deposit, palette="Set2")
plt.title("Distribution of Deposit Feature")
plt.xlabel("Subscribed to Deposit?")
plt.ylabel("Count")
plt.savefig(folder / "deposit_distribution.png")
plt.close()


pd_sample = df.select("age", "deposit").sample(False, 0.05, seed=42).toPandas()

plt.figure(figsize=(8, 5))
sns.boxplot(x="deposit", y="age", data=pd_sample, palette="Pastel1")
plt.title("Age Distribution by Deposit Subscription")
plt.xlabel("Deposited (Yes/No)")
plt.ylabel("Age")
plt.savefig(folder / "age_vs_deposit.png")
plt.close()

print("Visualizations saved successfully as PNG images in your apps directory!")

print("\nClient with the biggest balance:")

df.orderBy(F.col("balance").desc()).select("balance", "job", "age").show(1)

avg_balance = df.select(F.avg("balance")).first()[0]
twice_avg = avg_balance * 2

total_clients = df.count()
rich_clients = df.filter(F.col("balance") > twice_avg).count()

proportion = rich_clients / total_clients

print(f"Average Balance: {avg_balance:.2f}")
print(f"Proportion of clients with balance > twice the average: {proportion:.2%}")

print("\nDeposit success rate by Education level:")
df.groupBy("education") \
  .agg(F.round(F.avg(F.when(F.col("deposit") == "yes", 1).otherwise(0)),2).alias("deposit_rate")) \
  .orderBy(F.col("deposit_rate").desc()) \
  .show()

df_numeric_target = df.withColumn("deposit_binary", F.when(F.col("deposit") == "yes", 1).otherwise(0))

print("\nCorrelation with Deposit (Numerical Variables):")
for col in numerical_cols:
    if col in df.columns:
        corr_val = df_numeric_target.stat.corr("deposit_binary", col)
        print(f"    Correlation between deposit and {col}: {corr_val:.2f}")