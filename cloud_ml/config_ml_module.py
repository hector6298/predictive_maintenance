import os
import argparse
import json

from datetime import datetime
from azureml.core.conda_dependencies import CondaDependencies 
from azureml.core.webservice import Webservice, AciWebservice
from azureml.core.model import InferenceConfig, Model
from azureml.core import Workspace, Environment
from azureml.core.webservice import AciWebservice


def get_workspace_from_config():
    # Initialize workspace object from existing configuration
    ws = Workspace.from_config()
    print("Successfuly retrieved ML workspace:", 
            ws.name, 
            ws.resource_group, 
            ws.location, 
            ws.subscription_id, sep='\n')
    return ws


def create_conda_env(conda_packages, pip_packages, env_out_dir):
    myenv = CondaDependencies.create(
        conda_packages=conda_packages,
        pip_packages=pip_packages)

    with open(env_out_dir,"w") as f:
        f.write(myenv.serialize_to_string())
    print("Successfuly defined the conda environment")
    return myenv


def create_model_package(ws, 
                         model_name, 
                         entry_script, 
                         conda_file, 
                         image_name, 
                         package_out_dir):
    model_list = Model.list(ws,
                            name=model_name,
                            latest=True)

    if len(model_list) > 0:
        model = model_list[0]
        print(f"Loading registered model {model.name} with version {model.version}")
    else:
        raise Exception("No model could be found. Have you run the submit_train.py script?")


    inference_config = InferenceConfig(entry_script=entry_script,
                                    conda_file=conda_file,
                                    runtime="python",
                                    base_image="arm32v7/python:3.7-slim-buster",
                                    description="IOT Edge anomaly detection demo")
    print("Finished definining inference configuration")

    package = Model.package(ws, 
                            model_list, 
                            inference_config, 
                            generate_dockerfile=True,
                            image_name=image_name,
                            image_label="latest")

    package.wait_for_creation(show_output=True)
    print("Finished packaging the model as a Docker container")

    # Download the package.
    package.save(package_out_dir)

    print(package.serialize())
    # Get the Azure container registry that the model/Dockerfile uses.
    acr=package.get_container_registry()
    print("Address:", acr.address)

    return package, acr, inference_config, model_list


def set_acr_credentials_actions(acr):
    # Set env variables for the github runner
    print(f"::set-output name=acr_server::{str(acr.address)}")
    print(f"::set-output name=acr_username::{str(acr.username)}")
    print(f"::set-output name=acr_pass::{str(acr.password)}")


def register_environment(image_name, ws, acr):
    model_env = Environment.from_docker_image(name=image_name,
                                            image=image_name,
                                            container_registry=acr)

    model_env.register(ws)
    print("Done registering environment")


def setup_aci_test(ws, model_list, inference_config):
    aci_config = AciWebservice.deploy_configuration(cpu_cores = 1, 
                                                memory_gb = 1, 
                                                tags = {'area': "iot", 'type': "classification"}, 
                                                description = 'IOT Edge anomaly detection demo')
    service = Model.deploy(workspace=ws,
                            name=f"testservice",
                            models=model_list,
                            inference_config=inference_config,
                            deployment_config=aci_config,
                            overwrite=True)
    service.wait_for_deployment(show_output=True)
    print("Done test deployment. Starting sample inference...")
    return service


def test_service(service):
    # Generate sample request
    test_sample = json.dumps({"messageCount": 1, "temperature": 21.17794693, "humidity": 25 })

    # transform json string into bytes
    test_sample = bytes(test_sample, encoding = 'utf8')

    # send data to service and return prediction
    prediction = service.run(input_data = test_sample)
    print(prediction)


if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument('--model-name', type=str,
                        dest='model_name', help='Name for registered model.')
    parser.add_argument('--image-name', type=str,
                        dest='image_name', help='Name for the docker image.')
    args = parser.parse_args()

    # Variables
    model_name = args.model_name
    image_name = args.image_name
    aci_service_name = 'tempsensor-iotedge-ml-1'
    conda_packages = ['pandas', 'scikit-learn', 'numpy', 'pip=20.1.1']
    pip_packages = ['azureml-sdk', 'azureml-defaults']
    env_out_dir = 'saved_envs/myenv.yml'
    entry_script = 'cloud_ml/scripts_to_submit/iot_score.py'
    conda_file = 'saved_envs/myenv.yml'
    package_out_dir = "iot_edge/humid_telemetry/modules/ml_inference"

    # Execute tasks
    ws = get_workspace_from_config()
    myenv = create_conda_env(conda_packages, pip_packages, env_out_dir)
    package, acr, inference_config, model_list = create_model_package(
            ws, model_name, entry_script, conda_file, image_name, package_out_dir)
    set_acr_credentials_actions(acr)
    register_environment(image_name, ws, acr)
    service = setup_aci_test(ws, model_list, inference_config)
    test_service(service)