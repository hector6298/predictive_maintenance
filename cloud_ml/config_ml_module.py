import os
import argparse
import logging

from datetime import datetime
from azureml.core.model import Model
from azureml.core import Workspace
from azureml.core.authentication import AzureCliAuthentication


def get_workspace_from_config():
    # Initialize workspace object from existing configuration
    cli_auth = AzureCliAuthentication()

    ws = Workspace.get(name=workspace_name, 
                       subscription_id=subscription_id, 
                       resource_group=resource_group,
                       auth=cli_auth)

    logging.info("Successfuly retrieved ML workspace:", 
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
        logging.info(f"Loading registered model {model.name} with version {model.version}")
    else:
        raise Exception("No model could be found. Have you run the submit_train.py script?")

    model.download(model_path_out)


def set_model_path(model_path_out):
    logging.info(f"::set-output name=model_path::{str(model_path_out)}")


if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument('--model-name', type=str,
                        dest='model_name', help='Name for registered model.')
    parser.add_argument('--model-path-out', type=str,
                        dest='model_path_out', help='Output path for the model.')
    parser.add_argument('--resource-group', type=str,
                        dest='resource_group', help='Your resource group.')
    parser.add_argument('--workspace-name', type=str,
                        dest='workspace_name', help='The Azure ML workspace name.')
    parser.add_argument('--subscription-id', type=str,
                        dest='subscription_id', help='The Id of your Azure subscription.')
    args = parser.parse_args()

    # Variables
    model_name = args.model_name
    model_path_out = args.model_path_out
    subscription_id = args.subscription_id
    workspace_name = args.workspace_name
    resource_group = args.resource_group

    # Execute tasks
    ws = get_workspace_from_config()
    create_model_package(ws, model_name, model_path_out)
    set_model_path(model_path_out)