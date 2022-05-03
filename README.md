# predictive_maintenance

Predictive maintenance refers to the use of data-driven, proactive maintenance methods that are designed to analyze the condition of equipment and help predict when maintenance should be performed.

This repository holds the neccessary components to:

- Setup Cloud infrastructure 
- Setup machine learning workspace and automate ML training on the cloud.
- Setup containers for edge devices
  - produce and forward telemetry to cloud
  - Predict anomalies using pre-trained ML model

## Preliminaries

This repository was built in a way that infrastructure is created for you using and apache airflow DAG. However there are some manual steps that are currently not automated.

First you should have a Microsoft Azure Account and a valid subscription. If you don't have, click [here](https://signup.azure.com/) to sign up. After that, you should install the [azure cli client](https://docs.microsoft.com/en-us/cli/azure/install-azure-cli-linux?pivots=apt).

Now, create a resource group with a name of your preference (ex: "predictive_maintenance_rg"):

```
az group create -l westus2 -n predictive_maintenance_rg
```
Using that resource group and your subscription ID, create a service principal. This will allow the infrastructure pipelines to log into azure without interacting with the browser.

```
az ad sp create-for-rbac --name sp_predictive_maintenance \
                         --role owner \
                         --scopes /subscriptions/mySubscriptionID/resourceGroups/streaming_pdm
```

## Todo

- send data from hub to data lake
  - test data lake services or plain blob storage
- develop CI/CD workflow for cntinuous training
- Business model 

## Already done

- Package ML model as Docker image
- Test deployment of docker image into IoT Edge device.
- Test telemetry ingestion from hub to device
- create module to send predictioms back to hub
- explore real time dashboard methodologies.
