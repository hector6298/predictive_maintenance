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
    "dag_id": "training_dag",
    "default_args": default_args,
    "start_date": datetime.now(),
    "schedule_interval": None,
}

with DAG(**dag_args) as dag:

    t0 = BashOperator(
        task_id='az_login',
        bash_command=""" az login --service-principal \
                                  --username {{ var.json.training_config.service_principal.username_secret }} \
                                  --password {{ var.json.training_config.service_principal.password }} \
                                  --tenant {{ var.json.training_config.service_principal.tenant_secret }} 
        """
    )

    t1 = BashOperator(
        task_id='submit_train',
        bash_command="""python3 /opt/airflow/cloud_ml/submit_train.py \
                            --workspace-name "{{ var.json.training_config.aml.workspace_name }}" \
                            --training-script "{{ var.json.training_config.training_script }}" \
                            --script-path "{{ var.json.training_config.script_path }}" \
                            --subscription-id "{{ var.json.training_config.service_principal.subscription_id }}" \
                            --data-path "{{ var.json.training_config.data_path }}" \
                            --data-file "{{ var.json.training_config.data_file }}" \
                            --resource-group "{{ var.json.training_config.aml.resource_group }}" \
                            --model-name "{{ var.json.training_config.model_name }}" 
        """
    )

    t2 = BashOperator(
        task_id='config_ml_module',
        bash_command="""python3 /opt/airflow/cloud_ml/config_ml_module.py \
                                --model-name  {{ var.json.training_config.model_name }} \
                                --model-path-out  {{ var.json.training_config.model_path_out }} \
                                --subscription-id "{{ var.json.training_config.service_principal.subscription_id }}" \
                                --resource-group "{{ var.json.training_config.aml.resource_group }}" \
                                --workspace-name "{{ var.json.training_config.aml.workspace_name }}"  
        """                     
    )

t0 >> t1 >> t2

