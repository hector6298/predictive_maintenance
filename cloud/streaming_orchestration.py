# Databricks notebook source
# MAGIC %md
# MAGIC ## Defitinion of variables

# COMMAND ----------

dbutils.widgets.text("connectionStringEndPoint", '')
dbutils.widgets.text("eventHubName", '')
dbutils.widgets.text("consumerGroup", '')
dbutils.widgets.text("streamDebugMode", '')

connectionStringEndPoint = dbutils.widgets.get("connectionStringEndPoint")
eventHubName = dbutils.widgets.get("eventHubName")
consumerGroup = dbutils.widgets.get("consumerGroup")
streamDebugMode = dbutils.widgets.get("streamDebugMode")

# COMMAND ----------

# MAGIC %md Data acquisition and aggregation notebooks and args

# COMMAND ----------

hub2deltaNb = './hub_delta_ingestion_py'

# COMMAND ----------

if streamDebugMode:
    outputTableTelemetry = 'debug_telemetry_data'
    
hub2deltaArgs = {
    'connectionStringEndPoint': connectionStringEndPoint,
    'eventHubName': eventHubName,
    'consumerGroup': consumerGroup,
    'streamDebugMode': streamDebugMode,
}

# COMMAND ----------

# MAGIC %md Execute data acquisition

# COMMAND ----------

dbutils.notebook.run(hub2deltaNb, 0, hub2deltaArgs)
