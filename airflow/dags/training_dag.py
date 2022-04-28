from datetime import datetime, timedelta
from textwrap import dedent
from airflow import DAG
from airflow.operators.bash import BashOperator


default_args = {
    "email": "{{ var.yaml.training_config.notification_email }}",
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
                                  --username {{ var.yaml.training_config.service_principal.username_secret }} \
                                  --password {{ var.yaml.training_config.service_principal.password }} \
                                  --tenant {{ var.yaml.training_config.service_principal.tenant_secret }} 
        """
    )

    t1 = BashOperator(
        task_id='submit_train',
        bash_command="""python airflow/clud_ml/submit_train.py \
                                --model-name  {{ var.yaml.training.model_name }} \
                                --data-path {{ var.yaml.training.data_path }}    
        """
    )

    t2 = BashOperator(
        task_id='config_ml_module',
        bash_command="""python airflow/clud_ml/config_ml_module.py \
                                --model-name  {{ var.yaml.training.model_name }} \
                                --model-path-out  {{ var.yaml.training.model_path_out }}
        """
    )

t0 >> t1 >> t2

