-- Databricks notebook source
-- MAGIC %md
-- MAGIC ## Dev db

-- COMMAND ----------

CREATE DATABASE pdm_dev

-- COMMAND ----------

CREATE OR REPLACE TABLE pdm_dev.telemetry_data (
  message_id int,
  date_enqueued date,
  hour_enqueued integer,
  enqueued_time timestamp,
  device_id string,
  temperature double,
  humidity double
) USING delta

-- COMMAND ----------

CREATE OR REPLACE TABLE pdm_dev.telemetry_data_aggregated (
  start_time timestamp,
  end_time timestamp,
  mean_temp double,
  std_temp double,
  min_temp double,
  max_temp double,
  mean_humid double,
  std_humid double,
  min_humid double,
  max_humid double
) USING delta

-- COMMAND ----------

ALTER TABLE pdm_dev.telemetry_data SET TBLPROPERTIES (delta.autoOptimize.optimizeWrite = true, delta.autoOptimize.autoCompact = true);
ALTER TABLE pdm_dev.telemetry_data_aggregated SET TBLPROPERTIES (delta.autoOptimize.optimizeWrite = true, delta.autoOptimize.autoCompact = true);

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ## Prod db

-- COMMAND ----------

CREATE DATABASE pdm_prod

-- COMMAND ----------

CREATE OR REPLACE TABLE pdm_prod.telemetry_data (
  message_id int,
  date_enqueued date,
  hour_enqueued integer,
  enqueued_time timestamp
  device_id string,
  temperature double,
  humidity double
) USING delta

-- COMMAND ----------

CREATE OR REPLACE TABLE pdm_prod.telemetry_data_aggregated (
  start_time timestamp,
  end_time timestamp,
  mean_temp string,
  std_temp string,
  min_temp string,
  max_temp string,
  mean_humid string,
  std_humid string,
  min_humid string,
  max_humid string
) USING delta

-- COMMAND ----------

ALTER TABLE pdm_prod.telemetry_data SET TBLPROPERTIES (delta.autoOptimize.optimizeWrite = true, delta.autoOptimize.autoCompact = true);
ALTER TABLE pdm_prod.telemetry_data_aggregated SET TBLPROPERTIES (delta.autoOptimize.optimizeWrite = true, delta.autoOptimize.autoCompact = true);
