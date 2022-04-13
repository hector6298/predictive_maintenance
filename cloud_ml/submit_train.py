# Check core SDK version number
import azureml.core
import os
import argparse

from uuid import uuid4
from azureml.core import Workspace, Experiment, Environment, Dataset, ScriptRunConfig
from azureml.core.compute import ComputeTarget, RemoteCompute
from azureml.core.compute_target import ComputeTargetException
from azureml.core.compute import ComputeTarget, RemoteCompute
from azureml.core.compute_target import ComputeTargetException
from azureml.core.conda_dependencies import CondaDependencies
from azureml.widgets import RunDetails
from azureml.exceptions import ActivityFailedException



def get_workspace_from_config():
    # Initialize workspace object from existing configuration
    ws = Workspace.from_config()
    print("Successfuly retrieved ML workspace:", 
            ws.name, 
            ws.resource_group, 
            ws.location, 
            ws.subscription_id, sep='\n')
    return ws


def get_datastore(ws):
    # Get the default datastore
    ds = ws.get_default_datastore()
    print("Successfuly retrieved Datastore:",
            ds.name, 
            ds.datastore_type, 
            ds.account_name, 
            ds.container_name, sep='\n')
    return ds


def upload_data_to_store(ds, train_data_filename, train_target_path):
    ds.upload_files([train_data_filename], target_path=train_target_path, overwrite=True)
    print("Successfuly uploaded files")

    # initialize Tabular dataset 
    dataset = Dataset.Tabular.from_parquet_files(ds.path(train_data_filename))
    return dataset


def use_remote_compute(ws, compute_target_name):
    # use an existing compute target
    attached_dsvm_compute = RemoteCompute(workspace=ws, name=compute_target_name)
    print('found existing:', attached_dsvm_compute.name)
    return attached_dsvm_compute


def create_conda_environment(pip_packages):
    # Create Anaconda environment for the training
    conda_env = Environment("conda-env")
    conda_env.python.conda_dependencies = CondaDependencies.create(pip_packages)
    print("Successfuly prepared conda environment for compute")
    return conda_env


def configure_run(dataset, script_folder, training_script_name, train_target_path, attached_dsvm_compute, conda_env):
    # Configure Run
    script_arguments = ['--data-dir', dataset.as_named_input(train_target_path)]
    src = ScriptRunConfig(source_directory=script_folder, 
                        script=training_script_name, 
                        # pass the dataset as a parameter to the training script
                        arguments=script_arguments,
                        compute_target = attached_dsvm_compute,
                        environment = conda_env) 
    print(f"Successfuly prepared script configuration for target path {train_target_path}")
    return src


def submit_experiment(ws, src, experiment_name):
    # Submit experiment
    exp = Experiment(workspace=ws, name=experiment_name)

    try:
        run = exp.submit(config=src)
        print("Successfully submited experiment run")
        print(run)
        run.wait_for_completion(show_output=True)
    except ActivityFailedException as error:
        raise Exception(f"There was an error in the experiment. See {run.id} in the Ml workspace for more information.")
    else:
        print("Successfuly finished training run!")
    return run


def register_model(run, trained_model_description, model_name):
    # Register trained model
    model = run.register_model(description = trained_model_description,
                            model_path=f"./outputs/{model_name}",
                            model_name=f"{model_name}",
                            tags = {'area': "anomaly", 'type': "classification"})
    print(f"Successfuly registered model {model.name} with version {model.version}")

    print("SUCCESS!")
    return model



if __name__ == "__main__":
    print("SDK version:", azureml.core.VERSION)

    parser = argparse.ArgumentParser()
    parser.add_argument('--model-name', type=str,
                        dest='model_name', help='Name for the model to be registered.')
    args = parser.parse_args()


    # Variables
    model_name = args.model_name
    module_name = "machinelearningmodule"
    experiment_name = 'train-on-remote-vm'
    compute_target_name = 'cpu-cluster'
    trained_model_description = 'My AutoML Model'
    train_data_filename = 'cloud_ml/sample_data/temperature_data.parquet'
    train_target_path = 'cloud_ml'
    vm_name = "predictive_maintenance_vm"
    vm_username = "pdmvm"
    training_script_name = 'ml_training.py'
    script_folder = './cloud_ml/scripts_to_submit'
    pip_packages=['scikit-learn',
                'azureml-sdk',
                'pandas',
                'azureml-dataset-runtime[pandas,fuse]']

    os.makedirs(script_folder, exist_ok=True)

    ws = get_workspace_from_config()
    resource_group = ws.resource_group
    subscription_id = ws.subscription_id
    ds = get_datastore(ws)
    dataset = upload_data_to_store(ds, train_data_filename, train_target_path)
    attached_dsvm_compute = use_remote_compute(ws, compute_target_name)
    conda_env = create_conda_environment(pip_packages)
    src = configure_run(dataset, script_folder, 
                        training_script_name, train_target_path, 
                        attached_dsvm_compute, conda_env)
    run = submit_experiment(ws, src, experiment_name)
    model = register_model(run, trained_model_description, model_name)