# Databricks notebook source
from pyspark.sql import functions as F
from pyspark.sql.functions import col, window
from datetime import datetime

# COMMAND ----------

dbutils.widgets.text("streamDebugMode", 'True')

streamDebugMode = dbutils.widgets.get("streamDebugMode")

if streamDebugMode:
    inputTelemetryTable = 'pdm_dev.telemetry_data'
    outputTable = 'pdm_dev.telemetry_data_aggregated'
else:
    inputTelemetryTable = 'pdm_prod.telemetry_data'
    outputTable = 'pdm_prod.telemetry_data_aggregated'

# COMMAND ----------

# MAGIC %md
# MAGIC ## Read stream from raw table

# COMMAND ----------

df = spark.readStream.format("delta").option("startingTimestamp", datetime.today().strftime('%Y-%m-%d')).table(inputTelemetryTable)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Perform aggregations

# COMMAND ----------

aggregations = [
    F.mean(col("temperature")).alias('mean_temp'),
    F.stddev(col("temperature")).alias('std_temp'),
    F.min(col("temperature")).alias('min_temp'),
    F.max(col("temperature")).alias('max_temp'),
    F.mean(col("humidity")).alias('mean_humid'),
    F.stddev(col("humidity")).alias('std_humid'),
    F.min(col("humidity")).alias('min_humid'),
    F.max(col("humidity")).alias('max_humid')
]

slidingWindows = df.withWatermark("enqueued_time", "2 minutes")\
                   .groupBy(window("enqueued_time", "2 minutes", "1 minutes"))\
                   .agg(*aggregations)

# COMMAND ----------

slidingWindows.createOrReplaceTempView("telemetry_data_aggs")

# COMMAND ----------

slidingWindows = spark.sql('''
    SELECT window.start as start_time,
           window.end as end_time,
           mean_temp,
           std_temp,
           min_temp,
           max_temp,
           mean_humid,
           std_humid,
           min_humid,
           max_humid
   FROM telemetry_data_aggs
''')

# COMMAND ----------

# MAGIC %md
# MAGIC ## Data sink for aggregated data

# COMMAND ----------

slidingWindows.writeStream\
              .format("delta")\
              .outputMode("append")\
              .option("checkpointLocation", f"/delta/events/_checkpoints/{outputTable.split('.')[1]}_ckpt")\
              .table(outputTable)

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT * from pdm_dev.telemetry_data_aggregated

# COMMAND ----------


