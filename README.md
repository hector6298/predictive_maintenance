# From IoT data generation to real-time dashboard
### Predictive Maintenance
**Note:** Please read the whole readme to know how to setup the whole project. **This is still a work in progress**.
## Overview

Predictive maintenance refers to the use of data-driven, proactive maintenance methods that are designed to analyze the condition of equipment and help predict when maintenance should be performed.

This repository holds the neccessary components to:

- Setup Cloud infrastructure 
- Setup machine learning workspace and automate ML training on the cloud.
- Setup containers for edge devices
  - produce and forward telemetry to cloud
  - Predict anomalies using pre-trained ML model

After setup, the project is designed so that the IoT Edge device produces data from sensor readings, then uses its machine learning module to predict anomalies and forwards the messages to IoT Hub. From IoT hub, these messages are consumed by an even hub object on the visualization server to build a real time dashboard. The concept of this project can be visualized as follows:

<img src="https://user-images.githubusercontent.com/41920808/166858148-4807cecd-23bb-4dce-ba81-e650b06aa793.png" width="800" height="400">

The design diagrams and documentation are also available on the wiki (work is still in progress).


## Preliminary steps on the cloud

This repository was built in a way that infrastructure is created for you using and apache airflow DAG. However there are some manual steps that are currently not automated. First, you should have a Microsoft Azure Account and a valid subscription. If you don't have, click [here](https://signup.azure.com/) to sign up. After that, you should install the [azure cli client](https://docs.microsoft.com/en-us/cli/azure/install-azure-cli-linux?pivots=apt).

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

now save the `username`, `password` and `tenant` fields as these will allow us to login using the CLI.

## Setting up Airflow

There are three pipelines that were created using apache airflow:
- Infrastructure setup
- Machine learning training on the cloud
- IoT modules building and deployment to edge device

Feel free to search about the architecture design of the three pipelines on the links in each item. Now, ensure that your computer has minimum requirements to run airflow. Furthermore, go to the `airflow` directory:

```
cd airflow
```

In the `docker-compose.yaml` file look for these lines:

```
  - ../cloud_ml:/opt/airflow/cloud_ml
  - ../iot_edge:/opt/airflow/iot_edge
```

These are directory mappings and will be mounted into the docker containers. `cloud_ml` contains script for setting up infrastructure and ML training on the cloud, while `iot_edge` contain dockerfiles, and iot edge modules to build the edge components. They are essential to setup the whole project. 

After that you will see a `Dockerfile` in the airflow folder. It starts from the latest airflow image and installs additional required libraries and packages. Some of them being the Docker client, which airflow will use to build docker images (yes inside the docker container but it actually uses the host system for the build process) and the azure cli to set-up cloud resources. 

After inspecting those files, build using docker compose:

```
docker-compose build
```

And initialize Airflow:

```
docker-compose up
```

You should be able to see the UI if you type `localhost:8080` in your browser.

## Executing the infrastructure pipeline

Take a look at the `airflow` folder:

```
airflow/
    configs/
        infrastructure_config.json # Configuration variables for infrastructure provisioning
        iotedge_config.json        # Configuration variables for iotedge modules building and deployment
        training_config.json       # Configuration variables for cloud ML training
    dags/
        infrastructure_dag.py      # Pipeline specification for infrastructure provisioning
        iotedge_dag.py             # Pipeline specification for iotedge modules building and deployment
        training_dag.py            # Pipeline specification for cloud ML training
    logs/
    plugins/
```
You can see that there are configuration `.json` files and airflow DAGs `.py` files. The configuration files are meant to be uploaded to airflow to serve as variables that can be retrieved by the DAGs for their execution. Each DAG is parameterized should you need to create another set of resources.

### 1. Setup the json files

You must insert values where there are placeholders. Optionally, you can also change the other parameters, but be mindfull that the aml workspace and IoT Hub are used on the other pipelines. This is an example of a configuration file:

```json
{
  "infrastructure_config": {
    "notification_email": "<email-for-notifications>",
    "subscription_id_secret": "<subscription-id>",
    "resource_group": "<az-resource-group>",
    "azure_region": "<region>",

    "service_principal": {
      "username_secret": "<sp-user>",
      "password": "<sp-pass>",
      "tenant_secret": "<tenant>"
    },
    "aml": {
      "workspace_name": "<name>"
    },
    "iot": {
      "iothub_name": "<iothub-name>",
      "iothub_sku": "<sku>",
      "storage_name": "<storage-account-name>",
      "container_name": "<storage-container-name>",
      "storage_endpoint_name_secret": "<name-for-your-endpoint>",
      "storage_route_name_secret": "<name-for-your-route>"
    }
  }
}
```

### 2. Upload the json files

Once the json files are updated, go to the airflow UI in your browser. In the "Admin" tab click on "Variables":

![image](https://user-images.githubusercontent.com/41920808/166608912-b418a4f2-527b-4844-8fee-b059b78f6545.png)

Then upload the infrastructure configuration file.

### 3. Run the DAG

After the variables are all set, you can now run the pipeline. The three pipelines were designed to be independent to execute them when needed. However, for a given resource group, you should only run the infrastructure_dag once. The other pipelines (2 and 3) should be executed whenever a new ML training must be performed.

On the Airflow UI go to DAGs tab:

![image](https://user-images.githubusercontent.com/41920808/166960633-a5d45a0c-c2ec-4f44-96b5-91987adc350a.png)

Select the `infrastructure_dag` DAG:

![image](https://user-images.githubusercontent.com/41920808/166960712-b56d7576-816f-4c12-a241-8fe1466b5a7b.png)

and hit the play button. The pipelines here are not meant to run periodically. They will only run manually.

## Connecting the IoT Edge device

For this example, a Raspberry Pi 3b+ is isued along with a DHT sensor that will produce the data. First, you need to setup the device by:

- Installing debian for raspberry Pi 
- Creating the device identity on IoT Hub
- Getting the device connection string 
- Installing the IoT Edge Runtime using the connection string
 
You can follow this document on how to do all of that.

<img src="https://user-images.githubusercontent.com/41920808/166963692-52212897-76f3-486f-b4ec-9892a23efd25.png" width="450" height="350">

For your particular pin configuration, you will have to go to the folder where the main script of the telemetry module is:

```
cd iot_edge/humid_telemetry/modules/send_telemetry
```
On your editor, change the imported pin to the one that you are particularly using. For instance, I am using `D17`:

```
from board import D17
```
then, save the script.

## Training the ML model and deploying the edge modules


## Initializing the real-time dashboard

From the root of the repository go to the `dashboard` folder:

```
cd dashboard
```
Install all the requirements:

```
pip3 install -r -requirements.txt
```
and run the panel server:

```
panel serve --show dashboard\bokeh_dashboard.py \
            --args --iothub-conn-str <iothub-builtin-endpoin> \
                   --iothub-consumer-group <iothub-consumer-group> \
                   --iothub-name <iothub-compatible-name>
```

Wait for the server to be ready and then, on your browser, go to `localhost:5050`. See the magic yourself. A dashboard should appear with real-time telemetry updates.

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
