from datetime import datetime, timedelta
from textwrap import dedent
from airflow import DAG
from airflow.operators.bash import BashOperator


default_args = {
    "email": "hectormrejia@gmail.com",
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 0,
}

dag_args = {
    "dag_id": "infrastructure_provisioning",
    "default_args": default_args,
    "start_date": datetime.now(),
    "schedule_interval": None,
}

with DAG(**dag_args) as dag:

    t0 = BashOperator(
        task_id='az_login',
        bash_command=""" az login --service-principal \
                                  --username {{ var.yaml.infrastructure_config.service_principal.username_secret }} \
                                  --password {{ var.yaml.infrastructure_config.service_principal.password }} \
                                  --tenant {{ var.yaml.infrastructure_config.service_principal.tenant_secret }} 
        """
    )

    t1 = BashOperator(
        task_id='config_aml_workspace',
        bash_command="""python airflow/cloud_ml/config_workspace.py \
                                --subscription-id {{ var.yaml.infrastructure_config.subscription_id_secret }} \
                                --resource-group {{ var.yaml.infrastructure_config.resource_group }} \
                                --azure-region  {{ var.yaml.infrastructure_config.azure_region }} \
                                --aml-workspace  {{ var.yaml.infrastructure_config.aml.workspace_name }}
        """
    )

    t2 = BashOperator(
        task_id='config_iot_workspace',
        bash_command="""az iot hub create --name {{ var.yaml.infrastructure_config.iot.iothub_name }} \
                                          --resource-group {{ var.yaml.infrastructure_config.resource_group }} \
                                          --sku {{ var.yaml.infrastructure_config.iot.iothub_sku }} \
                                          --location {{ var.yaml.infrastructure_config.azure_region }} 
        """
    )

    t3 = BashOperator(
        task_id='create_storage_account',
        bash_command="""az storage account create \
                                        --name {{ var.yaml.infrastructure_config.iot.storage_name }} \
                                        --resource-group {{ var.yaml.infrastructure_config.resource_group }} \
                                        --location {{ var.yaml.infrastructure_config.azure_region }}  \
                                        --sku {{ var.yaml.infrastructure_config.iot.storage_sku }}  \
                                        --kind {{ var.yaml.infrastructure_config.iot.storage_kind }} 
        """
    )

    t4 = BashOperator(
        task_id='get_storage_conn',
        bash_command="""echo $(az storage account show-connection-string \
                                                    --name {{ var.yaml.infrastructure_config.iot.storage_name }} \
                                                    --query connectionString \
                                                    -o tsv)
        """,
        do_xcom_push=True
    )

    t5 = BashOperator(
        task_id='create_storage_container',
        bash_command="""az storage container create --name {{ var.yaml.infrastructure_config.iot.container_name }} \
                                                    --account-name {{ var.yaml.infrastructure_config.iot.storage_name }} \
                                                    --connection-string {{ ti.xcom_pull(task_ids='get_storage_conn') }}
        """                     
    )

    t6 = BashOperator(
        task_id='create_routing_endpoint',
        bash_command="""az iot hub routing-endpoint create \
                            --connection-string {{ ti.xcom_pull(task_ids='get_storage_conn') }} \
                            --endpoint-name {{ var.yaml.infrastructure_config.iot.storage_endpoint_name_secret }} \
                            --endpoint-resource-group {{ var.yaml.infrastructure_config.resource_group }} \
                            --endpoint-subscription-id {{ var.yaml.infrastructure_config.subscription_id_secret }} \
                            --endpoint-type azurestoragecontainer \
                            --hub-name {{ var.yaml.infrastructure_config.iot.iothub_name }} \
                            --container {{ var.yaml.infrastructure_config.iot.container_name }} \
                            --resource-group {{ var.yaml.infrastructure_config.resource_group }} \
                            --encoding avro
        """
    )

    t7 = BashOperator(
        task_id='create_storage_route',
        bash_command="""az iot hub route create \
                            --name {{ var.yaml.infrastructure_config.iot.storage_route_name_secret }} \
                            --hub-name {{ var.yaml.infrastructure_config.iot.iothub_name }} \
                            --source devicemessages \
                            --resource-group {{ var.yaml.infrastructure_config.resource_group }} \
                            --endpoint-name {{ var.yaml.infrastructure_config.iot.storage_endpoint_name_secret }} \
                            --enabled \
        """
    )


t0 >> [t1,t2, t3] >> t4 >> t5 >> t6 >> t7