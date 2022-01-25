# Databricks notebook source
 from multiprocessing.pool import ThreadPool

# COMMAND ----------

# MAGIC %md
# MAGIC ## Defitinion of variables

# COMMAND ----------

dbutils.widgets.text("connectionStringEndPoint", '')
dbutils.widgets.text("eventHubName", '')
dbutils.widgets.text("consumerGroup", '')
dbutils.widgets.text("streamDebugMode", '')
dbutils.widgets.text("outputTableTelemetry", '')
dbutils.widgets.text("outputAggregationTable", '')

connectionStringEndPoint = dbutils.widgets.get("connectionStringEndPoint")
eventHubName = dbutils.widgets.get("eventHubName")
consumerGroup = dbutils.widgets.get("consumerGroup")
streamDebugMode = dbutils.widgets.get("streamDebugMode")
outputTableTelemetry = dbutils.widgets.get("outputTableTelemetry")
outputAggregationTable = dbutils.widgets.get("outputAggregationTable")

# COMMAND ----------

# MAGIC %md Data acquisition and aggregation notebooks and args

# COMMAND ----------

hub2deltaNb = './hub_delta_ingestion_py'
deltaFeatNb = './delta_feature_extraction'

# COMMAND ----------

if streamDebugMode:
    outputTableTelemetry = 'debug_telemetry_data'
    
hub2deltaArgs = {
    'connectionStringEndPoint': connectionStringEndPoint,
    'eventHubName': eventHubName,
    'consumerGroup': consumerGroup,
    'streamDebugMode': streamDebugMode,
    'outputTable': outputTableTelemetry
}

deltaFeatArgs = {
    'inputTelemetryTable': outputTableTelemetry,
    'streamDebugMode': streamDebugMode,
    'outputTable': outputAggregationTable
}

# COMMAND ----------

# MAGIC %md Execute data acquisition

# COMMAND ----------

#Run sub-notebooks in parallel
def runParallelNotebooks(workloads):
    pool = ThreadPool(len(workloads))
    return pool.map(
        lambda workload: dbutils.notebook.run(
            workload['notebookPath'],
            timeout_seconds=0,
            arguments = workload['params']),
    workloads)

workloads=[]

# COMMAND ----------

workloads.append({'notebookPath':hub2deltaNb, 'params':hub2deltaArgs})
workloads.append({'notebookPath':deltaFeatNb, 'params':deltaFeatArgs})


# COMMAND ----------

if len(workloads) > 0:
    paths = runParallelNotebooks(workloads)
    print(paths)
else:
    raise Exception("ERROR: No workloads present, terminating...")

# COMMAND ----------


