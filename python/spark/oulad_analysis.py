import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore")
from pyspark.sql import SparkSession
import pyspark.sql.functions as F
from pyspark.sql.window import Window
from pathlib import Path


spark = SparkSession.builder \
    .master("spark://spark-master:7077") \
    .appName("OULAD_Analytics") \
    .getOrCreate()

spark.sparkContext.setLogLevel("ERROR")

DATA_DIR = Path("/opt/spark/apps/oulad_data/")

assessments = spark.read.csv(str(DATA_DIR / "assessments.csv"), header=True, inferSchema=True)
courses = spark.read.csv(str(DATA_DIR / "courses.csv"), header=True, inferSchema=True)
vle = spark.read.csv(str(DATA_DIR / "vle.csv"), header=True, inferSchema=True)
studentInfo = spark.read.csv(str(DATA_DIR / "studentInfo.csv"), header=True, inferSchema=True)
studentRegistration = spark.read.csv(str(DATA_DIR / "studentRegistration.csv"), header=True, inferSchema=True)
studentAssessment = spark.read.csv(str(DATA_DIR / "studentAssessment.csv"), header=True, inferSchema=True)
studentVle = spark.read.csv(str(DATA_DIR / "studentVle.csv"), header=True, inferSchema=True)

print("Tables loaded successfully!")

print("\nStudent Info Schema")
studentInfo.printSchema()

print("\nStudent VLE Activity Sample")
studentVle.show(5)

###################################################################################
print("\nq07 - Do students tend to get higher or lower grades over the course of their studies?")
submissionOrder = Window.partitionBy("id_student", "code_module", "code_presentation").orderBy(F.col("date_submitted"))

ranked_scores = studentAssessment.join(assessments, on="id_assessment", how="inner") \
    .where(F.col("assessment_type") != "Exam") \
    .withColumn("submission_order", F.rank().over(submissionOrder)) \
    .withColumn("total_submissions", F.count("*").over(submissionOrder))

final_analysis = ranked_scores.groupBy("code_module", "code_presentation") \
    .agg(
        F.round(F.avg(
            F.when(F.col("submission_order") == 1, F.col("score"))
        ), 2).alias("initial_avg_score"),
        F.round(F.avg(
            F.when((F.col("submission_order") == F.col("total_submissions")) & (F.col("total_submissions") > 1), F.col("score"))
        ), 2).alias("final_avg_score")
    )

result_df = final_analysis \
    .withColumn("avg_improvement", F.round(F.col("final_avg_score") - F.col("initial_avg_score"), 2)) \
    .orderBy(F.col("avg_improvement").desc())

result_df.show()

###################################################################################
print("\nq08 - Are any of the student's characteristics (from studentInfo) "
      "good predictors to their academic achievements?")
def success_rates(by="highest_education"):
    aggregated_df = studentInfo.groupBy(by) \
        .agg(
        F.count("id_student").alias("total_students"),
        F.sum(
            F.when(F.col("final_result").isin("Pass", "Distinction"), 1).otherwise(0)
        ).alias("success_count"),
        F.sum(
            F.when(F.col("final_result") == "Distinction", 1).otherwise(0)
        ).alias("distinction_count"),
        F.sum(
            F.when(F.col("final_result") == "Withdrawn", 1).otherwise(0)
        ).alias("withdrawal_count")
    )
    result_df = aggregated_df \
        .withColumn("success_rate_pct", F.round((F.col("success_count") * 100) / F.col("total_students"), 2)) \
        .withColumn("distinction_rate_pct", F.round((F.col("distinction_count") * 100) / F.col("total_students"), 2)) \
        .withColumn("withdrawal_rate_pct", F.round((F.col("withdrawal_count") * 100) / F.col("total_students"), 2)) \
        .select(
        by,
        "total_students",
        "success_rate_pct",
        "distinction_rate_pct",
        "withdrawal_rate_pct"
    ).orderBy(F.col("success_rate_pct").desc())
    result_df.show(truncate=False)

success_rates(by="highest_education")
success_rates(by="gender")
success_rates(by="disability")

###################################################################################
print("\nq09 - Do courses get more/less difficult between presentations?")
joined_df = studentInfo.join(
    studentAssessment,
    on="id_student",
    how="left"
)
analytics_df = joined_df.groupBy("code_module", "code_presentation") \
    .agg(
    F.round(F.avg("score"), 2).alias("avg_score"),
    F.count_distinct(
        F.when(F.col("final_result") == "Fail", F.col("id_student"))
    ).alias("fail_count"),
    F.count_distinct("id_student").alias("student_count")
)
result_df = analytics_df \
    .withColumn(
        "fail_rate_pct",
        F.round((F.col("fail_count") * 100) / F.col("student_count"), 2)
    ).select("code_module", "code_presentation", "avg_score", "fail_rate_pct", "student_count") \
    .orderBy("code_module", "code_presentation")
result_df.show()

###################################################################################
print("\nq10 - Are there any common combinations of courses that students take simultaneously / in a specific order?")
s1 = studentInfo.alias("s1")
s2 = studentInfo.alias("s2")

co_registration_df = s1.join(
    s2,
    (F.col("s1.id_student") == F.col("s2.id_student")) &
    (F.col("s1.code_presentation") == F.col("s2.code_presentation")) &
    (F.col("s1.code_module") < F.col("s2.code_module")),
    how="inner"
)

result_df = co_registration_df.groupBy(
        F.col("s1.code_presentation").alias("semester"),
        F.col("s1.code_module").alias("module_a"),
        F.col("s2.code_module").alias("module_b")
    ) \
    .agg(F.count_distinct("s1.id_student").alias("student_count")) \
    .orderBy(F.col("student_count").desc())

result_df.show(20, truncate=False)

###################################################################################
print("\nq11 - Are assessments with lower weight prone to being easier?")
joined_df = assessments.join(
    studentAssessment,
    on="id_assessment",
    how="inner"
).where((F.col("assessment_type") != "Exam") & (F.col("weight") > 0))

result_df = joined_df.groupBy(F.col("weight")) \
    .agg(F.count_distinct("id_assessment").alias("number_of_assessments"),
         F.round(F.avg("score"), 2).alias("avg_score")) \
    .orderBy(F.col("weight").asc())

result_df.show(truncate=False)

###################################################################################
print("\nq12 - Are there specific times when students tend to cancel their\n"
      "registrations? Is it relative to course start/assessments/exams or is it specific time of the year?")

categorized_df = studentRegistration.withColumn(
    "cancellation_window",
    F.when(F.col("date_unregistration") < 0, "Before Start")
     .when(F.col("date_unregistration").between(0, 30), "Month 1")
     .when(F.col("date_unregistration").between(31, 90), "Months 2-3")
     .when(F.col("date_unregistration") > 90, "After month 3")
     .otherwise("Finished Course")
)

result_df = categorized_df.groupBy("cancellation_window") \
    .agg(F.count("*").alias("student_count"))

result_df.show(truncate=False)

###################################################################################
print("\nq13 - Do specific \"kinds\" of students use VLE more than others?")
clicks_per_student = studentVle.groupBy("id_student") \
    .agg(F.sum("sum_click").alias("total_clicks"))

joined_df = studentInfo.join(
    clicks_per_student,
    on="id_student",
    how="inner"
)
result_df = joined_df.groupBy("age_band") \
    .agg(F.round(F.avg("total_clicks"), 2).alias("avg_clicks_per_student")) \
    .orderBy(F.col("avg_clicks_per_student").asc())

result_df.show(truncate=False)
