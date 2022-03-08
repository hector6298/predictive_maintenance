# Check core SDK version number
import azureml.core
from uuid import uuid4

from azureml.core import Workspace, Experiment, Environment, Dataset, ScriptRunConfig
from azureml.core.compute import ComputeTarget, RemoteCompute
from azureml.core.compute_target import ComputeTargetException
from azureml.core.compute import ComputeTarget, RemoteCompute
from azureml.core.compute_target import ComputeTargetException
from azureml.core.conda_dependencies import CondaDependencies
from azureml.widgets import RunDetails

print("SDK version:", azureml.core.VERSION)


ws = Workspace.from_config()
print(ws.name, ws.resource_group, ws.location, ws.subscription_id, sep='\n')

experiment_name = 'train-on-remote-vm'
exp = Experiment(workspace=ws, name=experiment_name)


# Get the default datastore
ds = ws.get_default_datastore()
print(ds.name, ds.datastore_type, ds.account_name, ds.container_name)

ds.upload_files(['./features.npy', './labels.npy'], target_path='diabetes', overwrite=True)

# initialize file dataset 
ds_paths = [(ds, 'diabetes/')]
dataset = Dataset.File.from_files(path = ds_paths)


compute_target_name = 'cpudsvm'
# if you want to connect using SSH key instead of username/password you can provide parameters private_key_file and private_key_passphrase 
try:
    attached_dsvm_compute = RemoteCompute(workspace=ws, name=compute_target_name)
    print('found existing:', attached_dsvm_compute.name)
except ComputeTargetException:
    attach_config = RemoteCompute.attach_configuration(resource_id='<resource_id>',
                                                       ssh_port=22,
                                                       username='username',
                                                       private_key_file='./.ssh/id_rsa')
    attached_dsvm_compute.wait_for_completion(show_output=True)


conda_env = Environment("conda-env")
conda_env.python.conda_dependencies = CondaDependencies.create(pip_packages=['scikit-learn',
                                                                             'azureml-sdk',
                                                                             'azureml-dataset-runtime[pandas,fuse]'])


script_arguments = ['--data-folder', dataset.as_named_input('diabetes').as_mount('/tmp/{}'.format(uuid4()))]
src = ScriptRunConfig(source_directory=script_folder, 
                      script='train.py', 
                      # pass the dataset as a parameter to the training script
                      arguments=script_arguments,
                      compute_target = attached_dsvm_compute,
                      environment = conda_env) 

run = exp.submit(config=src)
RunDetails(run).show()
run.wait_for_completion(show_output=True)

# Register trained model
description = 'My AutoML Model'
model = run.register_model(description = description,
                            tags={'area': 'qna'})
print(run.model_id)


attached_dsvm_compute.detach()