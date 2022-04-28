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
                                  --username {{ var.yaml.iotedge_config.service_principal.username_secret }} \
                                  --password {{ var.yaml.iotedge_config.service_principal.password }} \
                                  --tenant {{ var.yaml.iotedge_config.service_principal.tenant_secret }} 
        """
    )

    # Build process for send telemetry

    t1 = BashOperator(
        task_id='build_telemetry',
        bash_command="""docker build --platform linux/arm/v7 \
                                     -t aml/send_telemetry:latest \
                                     -t aml/send_telemetry:{{ var.yaml.iotedge_config.send_telemetry.image_version }} \
                                     -f "{{ var.yaml.iotedge_config.send_telemetry.build_path }}/Dockerfile.arm32v7" \
                                     {{ var.yaml.iotedge_config.send_telemetry.build_path }}
        """
    )

    t2 = BashOperator(
        task_id='tag_telemetry',
        bash_command="""docker tag aml/send_telemetry:latest \
                                   {{ var.yaml.iotedge_config.acr.server }}/aml/send_telemetry:latest &&\
                        docker tag {{ var.yaml.iotedge_config.acr.server }}/aml/send_telemetry:latest \
                                   {{ var.yaml.iotedge_config.acr.server }}/aml/send_telemetry:{{ var.yaml.iotedge_config.send_telemetry.image_version }}
        """
    )

    t3 = BashOperator(
        task_id='push_telemetry',
        bash_command="""docker push {{ var.yaml.iotedge_config.acr.server }}/aml/send_telemetry:latest && \
                        docker push {{ var.yaml.iotedge_config.acr.server }}/aml/send_telemetry:{{ var.yaml.iotedge_config.send_telemetry.image_version }}
        """
    )

    # Build process for temp model

    t4 = BashOperator(
        task_id='build_model',
        bash_command="""docker build --platform linux/arm/v7 \
                                     -t aml/temp_model:latest \
                                     -t aml/temp_model:{{ var.yaml.iotedge_config.temp_model.image_version }} \
                                     -f "{{ var.yaml.iotedge_config.temp_model.build_path }}/Dockerfile.arm32v7" \
                                     {{ var.yaml.iotedge_config.temp_model.build_path }}
        """
    )

    t5 = BashOperator(
        task_id='tag_model',
        bash_command="""docker tag aml/temp_model:latest \
                                   {{ var.yaml.iotedge_config.acr.server }}/aml/temp_model:latest &&\
                        docker tag {{ var.yaml.iotedge_config.acr.server }}/aml/temp_model:latest \
                                   {{ var.yaml.iotedge_config.acr.server }}/aml/temp_model:{{ var.yaml.iotedge_config.temp_model.image_version }}
        """
    )

    t6 = BashOperator(
        task_id='push_model',
        bash_command="""docker push {{ var.yaml.iotedge_config.acr.server }}/aml/temp_model:latest && \
                        docker push {{ var.yaml.iotedge_config.acr.server }}/aml/temp_model:{{ var.yaml.iotedge_config.temp_model.image_version }}
        """
    )

    t7 = BashOperator(
        task_id='config_deployment',
        bash_command="""python cloud_ml/config_deployment.py \
                                    --acr-server {{ var.yaml.iotedge_config.acr.server }} \
                                    --acr-username {{ var.yaml.iotedge_config.acr.username_secret }} \
                                    --acr-pass {{ var.yaml.iotedge_config.acr.password }} \
                                    --telemetry-image {{ var.yaml.iotedge_config.acr.server }}/aml/send_telemetry:latest \
                                    --inference-image {{ var.yaml.iotedge_config.acr.server }}/aml/temp_model:latest \
                                    --input-template {{ var.yaml.iotedge_config.deployment.input_template }} \
                                    --output-deployment {{ var.yaml.iotedge_config.deployment.output_deployment }} \
                                    --telemetry-version {{ var.yaml.iotedge_config.send_telemetry.module_version }} \
                                    --classification-version {{ var.yaml.iotedge_config.temp_model.module_version }}
        """
    )

    t8 = BashOperator(
        task_id='deploy_edge_modules',
        bash_command="""az iot edge set-modules --device-id {{ var.yaml.iotedge_config.device_id }} \
                                                --login {{ var.yaml.iotedge_config.hub_endpoint }} \
                                                --content {{ var.yaml.iotedge_config.deployment.output_deployment }}
        """
    )

    t0 >> [t1, t4] >> [t2, t5] >> [t3, t6] >> t7 >> t8

