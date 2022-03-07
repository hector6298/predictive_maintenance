// Databricks notebook source
val connectionStringEndPoint = "Endpoint=sb://ihsuprodmwhres025dednamespace.servicebus.windows.net/;SharedAccessKeyName=iothubowner;SharedAccessKey=rkMaaaupaGY/sZ5cYb9Lk/yFy8FGB6+C096jg/DcjEs=;EntityPath=iothub-ehub-telemetry-17003703-f705eeecc7"
val eventHubName = "iothub-ehub-telemetry-17003703-f705eeecc7"
val consumerGroup = "databricksdelta"

// COMMAND ----------

import org.apache.spark.eventhubs._
import  org.apache.spark.eventhubs.{ ConnectionStringBuilder, EventHubsConf, EventPosition }
import  org.apache.spark.sql.functions.{ explode, split }

// To connect to an Event Hub, EntityPath is required as part of the connection string.
// Here, we assume that the connection string from the Azure portal does not have the EntityPath part.
val connectionString = ConnectionStringBuilder(connectionStringEndPoint)
  .setEventHubName(eventHubName)
  .build

val eventHubsConf = EventHubsConf(connectionString)
  .setStartingPosition(EventPosition.fromEndOfStream)
  .setConsumerGroup(consumerGroup)
  
val eventhubs = spark.readStream
  .format("eventhubs")
  .options(eventHubsConf.toMap)
  .load()

// COMMAND ----------

display(eventhubs)

// COMMAND ----------

import org.apache.spark.sql.types._ 
import org.apache.spark.sql.functions._

val schema = (new StructType)
    .add("temperature", DoubleType)
    .add("humidity", DoubleType)

val df = eventhubs.select(($"enqueuedTime").as("Enqueued_Time"),($"systemProperties.iothub-connection-device-id")
                  .as("Device_ID"),(from_json($"body".cast("string"), schema)
                  .as("telemetry_json"))).select("Enqueued_Time","Device_ID", "telemetry_json.*")

// COMMAND ----------

df.createOrReplaceTempView("device_telemetry_data")

// COMMAND ----------

val finalDF = spark.sql("Select Date(Enqueued_Time) as Date_Enqueued, Hour(Enqueued_Time) as Hour_Enqueued, Enqueued_Time, Device_ID, temperature AS Temperature, humidity as Humidity from device_telemetry_data")

// COMMAND ----------

finalDF.writeStream
  .outputMode("append")
  .option("checkpointLocation", "/delta/events/_checkpoints/etl-from-json")
  .format("delta")
  .partitionBy("Date_Enqueued", "Hour_Enqueued")
  .table("delta_telemetry_data")
