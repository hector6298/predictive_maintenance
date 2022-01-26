# Databricks notebook source
from pyspark.sql.functions import col, from_json, window
from pyspark.sql.types import StructType, DoubleType, IntegerType, StructField
from pyspark.sql import functions as F
from datetime import datetime
import json

# COMMAND ----------

# Widget definition
dbutils.widgets.text("connectionStringEndPoint", '')
dbutils.widgets.text("eventHubName", '')
dbutils.widgets.text("consumerGroup", '')
dbutils.widgets.text("streamDebugMode", 'True')

# Vars assignment to arguments
connectionStringEndPoint = dbutils.widgets.get("connectionStringEndPoint")
eventHubName = dbutils.widgets.get("eventHubName")
consumerGroup = dbutils.widgets.get("consumerGroup")
streamDebugMode = dbutils.widgets.get("streamDebugMode")

if streamDebugMode:
    outputTable = 'pdm_dev.telemetry_data'
    outputTableAgg = 'pdm_dev.telemetry_data_aggregated'
else:
    outputTable = 'pdm_prod.telemetry_data'
    outputTableAgg = 'pdm_prod.telemetry_data_aggregated'
    
# Create the positions
startingEventPosition = {
  "offset": -1,  
  "seqNo": -1,            #not in use
  "enqueuedTime": None,   #not in use
  "isInclusive": True
}

# COMMAND ----------

# MAGIC %md
# MAGIC ## Event Hubs streaming source definition

# COMMAND ----------

ehConf = {
    'eventhubs.connectionString': sc._jvm.org.apache.spark.eventhubs.EventHubsUtils.encrypt(connectionStringEndPoint),
    'eventhubs.consumerGroup': consumerGroup,
    'eventhubs.startingPosition': json.dumps(startingEventPosition)
}

# COMMAND ----------

df = spark \
  .readStream \
  .format("eventhubs") \
  .options(**ehConf) \
  .load()

# COMMAND ----------

# MAGIC %md
# MAGIC ## Parsing of telemetry data

# COMMAND ----------

schema = StructType([
    StructField("messageId", IntegerType(), True),
    StructField("temperature", DoubleType(), True),
    StructField("humidity", DoubleType(), True)
])

streamDf = df.select(col("enqueuedTime").alias("enqueued_time"),
                     col("systemProperties.iothub-connection-device-id").alias("device_id"),
                     from_json(col("body").cast("string"), schema).alias("telemetry_json"))\
             .select("enqueued_time", "device_id", "telemetry_json.*")


# COMMAND ----------

# MAGIC %md
# MAGIC ## Final format

# COMMAND ----------

streamDf.createOrReplaceTempView("device_telemetry_data")

# COMMAND ----------

streamDf = spark.sql("""
    SELECT messageId as message_id, 
           DATE(enqueued_time) as date_enqueued, 
           HOUR(enqueued_time) as hour_enqueued, 
           enqueued_time, 
           device_id, 
           temperature,
           humidity
    FROM device_telemetry_data
""")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Telemetry sink

# COMMAND ----------

spark.sparkContext.setLocalProperty("spark.scheduler.pool", "pool1")
streamDf.writeStream\
      .format("delta")\
      .outputMode("append")\
      .option("checkpointLocation", f"/delta/events/_checkpoints/{outputTable.split('.')[1]}")\
      .table(outputTable)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Rolling windows (feature extraction)

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
slidingWindows = streamDf.withWatermark("enqueued_time", "2 minutes")\
                   .groupBy(window("enqueued_time", "2 minutes", "1 minutes"))\
                   .agg(*aggregations)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Aggregation format

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
# MAGIC ## Aggregated data sink

# COMMAND ----------

spark.sparkContext.setLocalProperty("spark.scheduler.pool", "pool2")
slidingWindows.writeStream\
              .format("delta")\
              .outputMode("append")\
              .option("checkpointLocation", f"/delta/events/_checkpoints/{outputTable.split('.')[1]}_ckpt")\
              .table(outputTableAgg)

# COMMAND ----------

display(slidingWindows)
