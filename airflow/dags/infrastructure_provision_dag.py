from datetime import datetime, timedelta
from textwrap import dedent
from airflow import DAG
from airflow.operators.bash import BashOperator


default_args = {
    "email": "{{ var.json.training_config.notification_email }}",
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 0,
}

dag_args = {
    "dag_id": "infrastructure_provisioning_dag",
    "default_args": default_args,
    "start_date": datetime.now(),
    "schedule_interval": None,
}

with DAG(**dag_args) as dag:

    t0 = BashOperator(
        task_id='az_login',
        bash_command=""" az login --service-principal \
                                  --username {{ var.json.infrastructure_config.service_principal.username_secret }} \
                                  --password {{ var.json.infrastructure_config.service_principal.password }} \
                                  --tenant {{ var.json.infrastructure_config.service_principal.tenant_secret }} 
        """
    )

    t1 = BashOperator(
        task_id='create_acr',
        bash_command="""az acr create --resource-group {{ var.json.infrastructure_config.resource_group }} \
                                      --name {{ var.json.infrastructure_config.acr.name }} \
                                      --sku {{ var.json.infrastructure_config.acr.sku }} \
                                      --location {{ var.json.infrastructure_config.azure_region }}
        """
    )
    
    t1_1 = BashOperator(
        task_id='get_acr_id',
        bash_command="""echo $(az acr show --name {{ var.json.infrastructure_config.acr.name }} \
                                    --resource-group {{ var.json.infrastructure_config.resource_group }} \
                                    --query id \
                                    --output tsv)
        """,
        do_xcom_push=True
    )

    t2 = BashOperator(
        task_id="create_aml_workspace",
        bash_command="""az ml workspace create --name {{ var.json.infrastructure_config.aml.workspace_name }} \
                                          --resource-group {{ var.json.infrastructure_config.resource_group }} \
                                          --location {{ var.json.infrastructure_config.azure_region }} \
                                          --contrainer-registry {{ ti.xcom_pull(task_ids='get_acr_id') }}
        """
    )

    t3 = BashOperator(
        task_id="create_aml_compute",
        bash_command="""az ml compute create --name {{ var.json.infrastructure_config.aml.compute.name }} \
                                             --workspace-name {{ var.json.infrastructure_config.aml.workspace_name }} \
                                             --resource-group {{ var.json.infrastructure_config.resource_group }} \
                                             --max-instances {{ var.json.infrastructure_config.aml.compute.max }} \
                                             --min-instances {{ var.json.infrastructure_config.aml.compute.min }} \
                                             --size {{ var.json.infrastructure_config.aml.compute.node_type }}
        """
    ),


    t4 = BashOperator(
        task_id='config_iot_workspace',
        bash_command="""az iot hub create --name {{ var.json.infrastructure_config.iot.iothub_name }} \
                                          --resource-group {{ var.json.infrastructure_config.resource_group }} \
                                          --sku {{ var.json.infrastructure_config.iot.iothub_sku }} \
                                          --location {{ var.json.infrastructure_config.azure_region }} 
        """
    )

    t5 = BashOperator(
        task_id='create_storage_account',
        bash_command="""az storage account create \
                                        --name {{ var.json.infrastructure_config.iot.storage_name }} \
                                        --resource-group {{ var.json.infrastructure_config.resource_group }} \
                                        --location {{ var.json.infrastructure_config.azure_region }}  \
                                        --sku {{ var.json.infrastructure_config.iot.storage_sku }}  \
                                        --kind {{ var.json.infrastructure_config.iot.storage_kind }} 
        """
    )

    t6 = BashOperator(
        task_id='get_storage_conn',
        bash_command="""echo $(az storage account show-connection-string \
                                                    --name {{ var.json.infrastructure_config.iot.storage_name }} \
                                                    --query connectionString \
                                                    -o tsv)
        """,
        do_xcom_push=True
    )

    t7 = BashOperator(
        task_id='create_storage_container',
        bash_command="""az storage container create --name {{ var.json.infrastructure_config.iot.container_name }} \
                                                    --account-name {{ var.json.infrastructure_config.iot.storage_name }} \
                                                    --connection-string {{ ti.xcom_pull(task_ids='get_storage_conn') }}
        """                     
    )

    t8 = BashOperator(
        task_id='create_routing_endpoint',
        bash_command="""az iot hub routing-endpoint create \
                            --connection-string {{ ti.xcom_pull(task_ids='get_storage_conn') }} \
                            --endpoint-name {{ var.json.infrastructure_config.iot.storage_endpoint_name_secret }} \
                            --endpoint-resource-group {{ var.json.infrastructure_config.resource_group }} \
                            --endpoint-subscription-id {{ var.json.infrastructure_config.subscription_id_secret }} \
                            --endpoint-type azurestoragecontainer \
                            --hub-name {{ var.json.infrastructure_config.iot.iothub_name }} \
                            --container {{ var.json.infrastructure_config.iot.container_name }} \
                            --resource-group {{ var.json.infrastructure_config.resource_group }} \
                            --encoding avro
        """
    )

    t9 = BashOperator(
        task_id='create_storage_route',
        bash_command="""az iot hub route create \
                            --name {{ var.json.infrastructure_config.iot.storage_route_name_secret }} \
                            --hub-name {{ var.json.infrastructure_config.iot.iothub_name }} \
                            --source devicemessages \
                            --resource-group {{ var.json.infrastructure_config.resource_group }} \
                            --endpoint-name {{ var.json.infrastructure_config.iot.storage_endpoint_name_secret }} \
                            --enabled \
        """
    )


t0 >> t1 >> t1_1 >> t2 >> t3
[t4, t5] >> t6 >> t7 >> t8 >> t9