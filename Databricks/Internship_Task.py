# Databricks notebook source
# Creating schemas and generating data for bronze layer
from pyspark.sql.types import StructType, StructField, StringType, IntegerType, DoubleType
from pyspark.sql.functions import current_timestamp

# 1. Создаем схемы (data bases)
spark.sql("CREATE DATABASE IF NOT EXISTS bronze")
spark.sql("CREATE DATABASE IF NOT EXISTS silver")
spark.sql("CREATE DATABASE IF NOT EXISTS gold")

# 2. Generating data for taxi (including rows with Null values for filtration tests)
taxi_data = [
    (1, 2.5, 15.50, 1, 100, "2024-01-15 10:00:00", "2024-01-15 10:15:00"),
    (2, 5.0, 10.00, 2, 101, "2024-01-15 11:00:00", "2024-01-15 11:30:00"),
    (0, 0.0, 0.0, 3, 100, "2024-01-15 12:00:00", "2024-01-15 12:00:00"), # Bad data (filtration in Silver)
    (3, 8.2, 25.75, 1, 100, "2024-01-15 13:00:00", "2024-01-15 13:45:00"),
    (2, 3.1, 12.00, 4, 102, "2024-01-15 14:00:00", "2024-01-15 14:20:00")
]
taxi_schema = StructType([
    StructField("passenger_count", IntegerType(), True),
    StructField("trip_distance", DoubleType(), True),
    StructField("fare_amount", DoubleType(), True),
    StructField("payment_type", IntegerType(), True),
    StructField("PULocationID", IntegerType(), True),
    StructField("tpep_pickup_datetime", StringType(), True),
    StructField("tpep_dropoff_datetime", StringType(), True)
])
df_taxi = spark.createDataFrame(taxi_data, schema=taxi_schema)

# 3. Generating data for users (including rows with Null values)
users_data = [("Alice", "alice@test.com"), ("Bob", "bob@test.com"), (None, "null@test.com")]
users_schema = StructType([
    StructField("name", StringType(), True),
    StructField("email", StringType(), True)
])
df_users = spark.createDataFrame(users_data, schema=users_schema)

# 4. Saving data to Bronze as Delta tables
df_taxi.write.format("delta").mode("overwrite").saveAsTable("bronze.taxi")
df_users.write.format("delta").mode("overwrite").saveAsTable("bronze.users")

print("✅ Test data created and saved to Bronze layer!")
display(spark.sql("SELECT * FROM bronze.taxi"))

# COMMAND ----------

# drivers data generation through Faker + Schema Evolution

%pip install faker

from faker import Faker
from pyspark.sql.types import StructType, StructField, StringType, IntegerType, DoubleType, TimestampType
from pyspark.sql.functions import current_timestamp
import random

fake = Faker()

# Test data for drivers (version 1 - without phone)
drivers_data_v1 = []
for _ in range(10):
    drivers_data_v1.append((
        fake.name(),
        fake.license_plate(),
        random.randint(1, 10),  # experience
        round(random.uniform(1.0, 5.0), 1),  # rating
        fake.date_time_this_year()  # timestamp
    ))

drivers_schema_v1 = StructType([
    StructField("name", StringType(), True),
    StructField("car_number", StringType(), True),
    StructField("experience", IntegerType(), True),
    StructField("rating", DoubleType(), True),
    StructField("timestamp", TimestampType(), True)
])

df_drivers_v1 = spark.createDataFrame(drivers_data_v1, schema=drivers_schema_v1)

# Saving version 1 to bronze.drivers
df_drivers_v1.write.format("delta").mode("overwrite").saveAsTable("bronze.drivers")

print("✅ Version 1: bronze.drivers with 5 columns")
display(spark.sql("SELECT * FROM bronze.drivers LIMIT 5"))

# Saving the current version for Time Travel
version_history = spark.sql("DESCRIBE HISTORY bronze.drivers").collect()
print(f"\n📊 Version history: {len(version_history)} recording(s)")
for v in version_history:
    print(f"   Version {v['version']} - {v['timestamp']}")

# COMMAND ----------

from faker import Faker
from pyspark.sql.types import StructType, StructField, StringType, IntegerType, DoubleType, TimestampType
import random

fake = Faker()

# Geberating data with new column - phone (version 2)
drivers_data_v2 = []
for _ in range(5):
    drivers_data_v2.append((
        fake.name(),
        fake.license_plate(),
        random.randint(1, 10),
        round(random.uniform(1.0, 5.0), 1),
        fake.date_time_this_year(),
        fake.phone_number()
    ))

drivers_schema_v2 = StructType([
    StructField("name", StringType(), True),
    StructField("car_number", StringType(), True),
    StructField("experience", IntegerType(), True),
    StructField("rating", DoubleType(), True),
    StructField("timestamp", TimestampType(), True),
    StructField("phone", StringType(), True)
])

df_drivers_v2 = spark.createDataFrame(drivers_data_v2, schema=drivers_schema_v2)

# With option mergeSchema (Schema Evolution)
df_drivers_v2.write.format("delta").mode("append").option("mergeSchema", "true").saveAsTable("bronze.drivers")

print("✅ Version 2: New column 'phone' added through Schema Evolution")
display(spark.sql("SELECT * FROM bronze.drivers LIMIT 5"))

# Showing version history
print("\n📊 Version history:")
display(spark.sql("DESCRIBE HISTORY bronze.drivers"))

# COMMAND ----------

# MAGIC %sql
# MAGIC -- 1. Checking version 0 data
# MAGIC SELECT * FROM bronze.drivers VERSION AS OF 0;
# MAGIC
# MAGIC -- 2. Rollback the table to the version 0 (without phone)
# MAGIC RESTORE TABLE bronze.drivers TO VERSION AS OF 0;
# MAGIC
# MAGIC -- 3. Checking whether the phone column dissappeared
# MAGIC SELECT * FROM bronze.drivers LIMIT 5;
# MAGIC
# MAGIC -- 4. Refreshed version history
# MAGIC DESCRIBE HISTORY bronze.drivers;

# COMMAND ----------

# MAGIC %sql
# MAGIC -- Data transformation (Silver layer)
# MAGIC
# MAGIC -- 1. Data cleaning (taxi): filtering + CASE for payment_type + ingest_time
# MAGIC CREATE OR REPLACE TABLE silver.taxi AS
# MAGIC SELECT 
# MAGIC     passenger_count,
# MAGIC     trip_distance,
# MAGIC     fare_amount,
# MAGIC     PULocationID,
# MAGIC     tpep_pickup_datetime,
# MAGIC     tpep_dropoff_datetime,
# MAGIC     CASE 
# MAGIC         WHEN payment_type = 1 THEN 'Credit Card'
# MAGIC         WHEN payment_type = 2 THEN 'Cash'
# MAGIC         ELSE 'Other'
# MAGIC     END AS payment_description,
# MAGIC     current_timestamp() AS ingest_time
# MAGIC FROM bronze.taxi
# MAGIC WHERE passenger_count > 0 
# MAGIC   AND trip_distance > 0 
# MAGIC   AND fare_amount > 0;
# MAGIC
# MAGIC -- Removing duplicates
# MAGIC CREATE OR REPLACE TABLE silver.taxi_dedup AS
# MAGIC SELECT DISTINCT * FROM silver.taxi;
# MAGIC
# MAGIC -- 2. Data cleaning (users): filtering NULL + ingest_time
# MAGIC CREATE OR REPLACE TABLE silver.users AS
# MAGIC SELECT 
# MAGIC     name,
# MAGIC     email,
# MAGIC     current_timestamp() AS ingest_time,
# MAGIC     current_date() AS registration_date
# MAGIC FROM bronze.users
# MAGIC WHERE name IS NOT NULL;
# MAGIC
# MAGIC -- Checking the result
# MAGIC SELECT 'taxi_dedup' as table_name, COUNT(*) as rows_count FROM silver.taxi_dedup
# MAGIC UNION ALL
# MAGIC SELECT 'users', COUNT(*) FROM silver.users;

# COMMAND ----------

# MAGIC %sql
# MAGIC -- Silver.drivers: filtering + ingest_time
# MAGIC CREATE OR REPLACE TABLE silver.drivers AS
# MAGIC SELECT 
# MAGIC     name,
# MAGIC     car_number,
# MAGIC     experience,
# MAGIC     rating,
# MAGIC     timestamp,
# MAGIC     current_timestamp() AS ingest_time
# MAGIC FROM bronze.drivers
# MAGIC WHERE experience > 0 
# MAGIC   AND rating BETWEEN 1.0 AND 5.0;
# MAGIC
# MAGIC -- Removing duplicates
# MAGIC CREATE OR REPLACE TABLE silver.drivers_dedup AS
# MAGIC SELECT DISTINCT * FROM silver.drivers;
# MAGIC
# MAGIC -- Gold.driver_metrics: grouping by experience level
# MAGIC CREATE OR REPLACE TABLE gold.driver_metrics AS
# MAGIC SELECT 
# MAGIC     experience AS experience_level,
# MAGIC     COUNT(*) AS drivers_count,
# MAGIC     ROUND(AVG(rating), 2) AS avg_rating
# MAGIC FROM silver.drivers_dedup
# MAGIC GROUP BY experience
# MAGIC ORDER BY experience_level;
# MAGIC
# MAGIC -- Check
# MAGIC SELECT * FROM gold.driver_metrics;

# COMMAND ----------

# MAGIC %sql
# MAGIC -- Gold layer: aggregation
# MAGIC
# MAGIC -- 1. gold.taxi_metrics
# MAGIC CREATE OR REPLACE TABLE gold.taxi_metrics AS
# MAGIC SELECT 
# MAGIC     PULocationID,
# MAGIC     payment_description,
# MAGIC     COUNT(*) AS total_trips,
# MAGIC     ROUND(SUM(fare_amount), 2) AS total_revenue
# MAGIC FROM silver.taxi_dedup
# MAGIC GROUP BY PULocationID, payment_description;
# MAGIC
# MAGIC
# MAGIC -- 2. gold.user_metrics
# MAGIC CREATE OR REPLACE TABLE gold.user_metrics AS
# MAGIC SELECT 
# MAGIC     registration_date,
# MAGIC     COUNT(*) AS user_count
# MAGIC FROM silver.users
# MAGIC GROUP BY registration_date
# MAGIC ORDER BY user_count DESC;
# MAGIC
# MAGIC
# MAGIC -- Checking result
# MAGIC SELECT 'taxi_metrics' as table_name, COUNT(*) as rows FROM gold.taxi_metrics
# MAGIC UNION ALL
# MAGIC SELECT 'driver_metrics', COUNT(*) FROM gold.driver_metrics
# MAGIC UNION ALL
# MAGIC SELECT 'user_metrics', COUNT(*) FROM gold.user_metrics;

# COMMAND ----------

# 1. Driver directory with ID (source of truth)
df_drivers_reference = spark.sql("""
    SELECT 
        row_number() OVER (ORDER BY name) AS driver_id,
        name,
        car_number,
        experience,
        rating,
        timestamp,
        ingest_time
    FROM silver.drivers_dedup
""")

df_drivers_reference.write.format("delta").mode("overwrite").saveAsTable("silver.drivers_reference")

# 2. Assigning a random `driver_id` to the taxi from the range 1–N (where N = the number of drivers)
num_drivers = df_drivers_reference.count()

df_taxi_with_id = spark.sql(f"""
    SELECT 
        *,
        (abs(hash(PULocationID, passenger_count, fare_amount)) % {num_drivers}) + 1 AS driver_id
    FROM silver.taxi_dedup
""")

# 3. temporary view
df_taxi_with_id.createOrReplaceTempView("taxi_with_driver_id")
df_drivers_reference.createOrReplaceTempView("drivers_reference")

# 4. LEFT JOIN
df_enriched_trips = spark.sql("""
    SELECT 
        t.passenger_count,
        t.trip_distance,
        t.fare_amount,
        t.PULocationID,
        t.payment_description,
        t.tpep_pickup_datetime,
        t.tpep_dropoff_datetime,
        t.driver_id,
        d.name AS driver_name,
        d.car_number AS driver_car,
        d.experience AS driver_experience,
        d.rating AS driver_rating
    FROM taxi_with_driver_id t
    LEFT JOIN drivers_reference d ON t.driver_id = d.driver_id
""")

# 5. Saving
df_enriched_trips.write.format("delta").mode("overwrite").saveAsTable("gold.enriched_trips")

print(f"✅ gold.enriched_trips created! Drivers count: {num_drivers}")
display(df_enriched_trips)

# COMMAND ----------

# MAGIC %sql
# MAGIC -- FINAL MAINTENANCE STEP
# MAGIC
# MAGIC -- 1. File compaction and sorting (Z-Order)
# MAGIC OPTIMIZE gold.taxi_metrics ZORDER BY (PULocationID);
# MAGIC OPTIMIZE gold.driver_metrics ZORDER BY (experience_level);
# MAGIC OPTIMIZE gold.user_metrics ZORDER BY (registration_date);
# MAGIC OPTIMIZE gold.enriched_trips ZORDER BY (driver_id, PULocationID);
# MAGIC
# MAGIC -- 2. Cleaning up old file versions (VACUUM)
# MAGIC -- RETAIN 168 HOURS (7 days) - in order not to break Time Travel and concurrent reads
# MAGIC VACUUM gold.taxi_metrics RETAIN 168 HOURS;
# MAGIC VACUUM gold.driver_metrics RETAIN 168 HOURS;
# MAGIC VACUUM gold.user_metrics RETAIN 168 HOURS;
# MAGIC VACUUM gold.enriched_trips RETAIN 168 HOURS;
# MAGIC
# MAGIC -- Check: file size after optimization
# MAGIC DESCRIBE DETAIL gold.taxi_metrics;
# MAGIC DESCRIBE DETAIL gold.driver_metrics;
# MAGIC DESCRIBE DETAIL gold.user_metrics;
# MAGIC DESCRIBE DETAIL gold.enriched_trips;

# COMMAND ----------

import json
from datetime import datetime

# Collecting statistics across all tables
report = {
    "timestamp": datetime.now().isoformat(),
    "pipeline": "Internship_Task",
    "bronze": {
        "taxi": spark.sql("SELECT COUNT(*) as count FROM bronze.taxi").collect()[0]["count"],
        "users": spark.sql("SELECT COUNT(*) as count FROM bronze.users").collect()[0]["count"],
        "drivers": spark.sql("SELECT COUNT(*) as count FROM bronze.drivers").collect()[0]["count"]
    },
    "silver": {
        "taxi_dedup": spark.sql("SELECT COUNT(*) as count FROM silver.taxi_dedup").collect()[0]["count"],
        "users": spark.sql("SELECT COUNT(*) as count FROM silver.users").collect()[0]["count"],
        "drivers_dedup": spark.sql("SELECT COUNT(*) as count FROM silver.drivers_dedup").collect()[0]["count"]
    },
    "gold": {
        "taxi_metrics": spark.sql("SELECT COUNT(*) as count FROM gold.taxi_metrics").collect()[0]["count"],
        "driver_metrics": spark.sql("SELECT COUNT(*) as count FROM gold.driver_metrics").collect()[0]["count"],
        "user_metrics": spark.sql("SELECT COUNT(*) as count FROM gold.user_metrics").collect()[0]["count"],
        "enriched_trips": spark.sql("SELECT COUNT(*) as count FROM gold.enriched_trips").collect()[0]["count"]
    }
}

# Generating report
print("✅ Pipeline Execution Report:")
print(json.dumps(report, indent=2))