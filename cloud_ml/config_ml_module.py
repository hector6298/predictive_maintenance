import os
import argparse

from datetime import datetime
from azureml.core.model import Model
from azureml.core import Workspace


def get_workspace_from_config():
    # Initialize workspace object from existing configuration
    ws = Workspace.from_config()
    print("Successfuly retrieved ML workspace:", 
            ws.name, 
            ws.resource_group, 
            ws.location, 
            ws.subscription_id, sep='\n')
    return ws


def create_model_package(ws, 
                         model_name, 
                         model_path_out):
    model_list = Model.list(ws,
                            name=model_name,
                            latest=True)

    model = None

    if len(model_list) > 0:
        model = model_list[0]
        print(f"Loading registered model {model.name} with version {model.version}")
    else:
        raise Exception("No model could be found. Have you run the submit_train.py script?")

    model.download(model_path_out)


def set_model_path(model_path_out):
    print(f"::set-output name=model_path::{str(model_path_out)}")


if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument('--model-name', type=str,
                        dest='model_name', help='Name for registered model.')
    args = parser.parse_args()

    # Variables
    model_name = args.model_name
    model_path_out = "C:/Users/mejia/OneDrive/Documents/predictive_maintenance/iot_edge/humid_telemetry/modules/ml_inference/models"

    # Execute tasks
    ws = get_workspace_from_config()
    create_model_package(ws, model_name, model_path_out)
    set_model_path(model_path_out)