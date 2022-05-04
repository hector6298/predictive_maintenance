# Check core SDK version number
import azureml.core
import os
import argparse
import logging

from azureml.core import Workspace, Experiment, Environment, Dataset, ScriptRunConfig
from azureml.core.compute import  RemoteCompute
from azureml.core.conda_dependencies import CondaDependencies
from azureml.widgets import RunDetails
from azureml.exceptions import ActivityFailedException
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


def get_datastore(ws):
    # Get the default datastore
    ds = ws.get_default_datastore()
    logging.info("Successfuly retrieved Datastore:",
            ds.name, 
            ds.datastore_type, 
            ds.account_name, 
            ds.container_name, sep='\n')
    return ds


def upload_data_to_store(ds, train_data_filename, train_target_path):
    ds.upload_files([train_target_path + train_data_filename], target_path=train_target_path, overwrite=True)
    logging.info("Successfuly uploaded files")

    # initialize Tabular dataset 
    dataset = Dataset.Tabular.from_parquet_files(ds.path(train_target_path + train_data_filename))
    return dataset


def use_remote_compute(ws, compute_target_name):
    # use an existing compute target
    attached_dsvm_compute = RemoteCompute(workspace=ws, name=compute_target_name)
    logging.info('found existing:', attached_dsvm_compute.name)
    return attached_dsvm_compute


def create_conda_environment(pip_packages):
    # Create Anaconda environment for the training
    conda_env = Environment("conda-env")
    conda_env.python.conda_dependencies = CondaDependencies.create(pip_packages=pip_packages)
    logging.info("Successfuly prepared conda environment for compute")
    return conda_env


def configure_run(dataset, script_folder, training_script_name, train_target_path, train_data_filename, attached_dsvm_compute, conda_env):
    # Configure Run
    script_arguments = ['--data-dir', dataset.as_named_input("temperature_data")]
    src = ScriptRunConfig(source_directory=script_folder, 
                        script=training_script_name, 
                        # pass the dataset as a parameter to the training script
                        arguments=script_arguments,
                        compute_target = attached_dsvm_compute,
                        environment = conda_env) 
    logging.info(f"Successfuly prepared script configuration for target path {train_target_path}")
    return src


def submit_experiment(ws, src, experiment_name):
    # Submit experiment
    exp = Experiment(workspace=ws, name=experiment_name)

    try:
        run = exp.submit(config=src)
        logging.info("Successfully submited experiment run")
        logging.info(run)
        run.wait_for_completion(show_output=True)
    except ActivityFailedException as error:
        raise Exception(f"There was an error in the experiment. See {run.id} in the Ml workspace for more information.")
    else:
        logging.info("Successfuly finished training run!")
    return run


def register_model(run, trained_model_description, model_name):
    # Register trained model
    model = run.register_model(description = trained_model_description,
                            model_path=f"./outputs/{model_name}",
                            model_name=f"{model_name}",
                            tags = {'area': "anomaly", 'type': "classification"})
    logging.info(f"Successfuly registered model {model.name} with version {model.version}")

    logging.info("SUCCESS!")
    return model



if __name__ == "__main__":
    logging.info("SDK version:", azureml.core.VERSION)

    parser = argparse.ArgumentParser()
    parser.add_argument('--model-name', type=str,
                        dest='model_name', help='Name for the model to be registered.')
    parser.add_argument('--data-path', type=str,
                        dest='data_path', help='Directory path of the data to be used on modeling.')
    parser.add_argument('--data-file', type=str,
                        dest='data_file', help='File name of the data to be used on modeling.')
    parser.add_argument('--resource-group', type=str,
                        dest='resource_group', help='Your resource group.')
    parser.add_argument('--workspace-name', type=str,
                        dest='workspace_name', help='The Azure ML workspace name.')
    parser.add_argument('--training-script', type=str,
                        dest='training_script', help='The name of your training script.')
    parser.add_argument('--script-path', type=str,
                        dest='script_path', help='The path of your training script.')
    parser.add_argument('--subscription-id', type=str,
                        dest='subscription_id', help='The Id of your Azure subscription.')
    args = parser.parse_args()


    # Variables
    workspace_name = args.workspace_name
    model_name = args.model_name
    train_data_filename = args.data_file
    training_script_name = args.training_script
    script_folder = args.script_path
    resource_group = args.resource_group
    subscription_id = args.subscription_id
    train_target_path = args.data_path

    experiment_name = 'train-on-remote-vm'
    compute_target_name = 'cpu-cluster'
    trained_model_description = 'My AutoML Model'
    vm_name = "predictive_maintenance_vm"
    vm_username = "pdmvm"

    pip_packages=['scikit-learn',
                'azureml-sdk',
                'pandas',
                'azureml-dataset-runtime[pandas,fuse]']

    os.makedirs(script_folder, exist_ok=True)

    ws = get_workspace_from_config()
    ds = get_datastore(ws)
    dataset = upload_data_to_store(ds, train_data_filename, train_target_path)
    attached_dsvm_compute = use_remote_compute(ws, compute_target_name)
    conda_env = create_conda_environment(pip_packages)
    src = configure_run(dataset, script_folder, 
                        training_script_name, train_target_path, 
                        train_data_filename,
                        attached_dsvm_compute, conda_env)
    run = submit_experiment(ws, src, experiment_name)
    model = register_model(run, trained_model_description, model_name)