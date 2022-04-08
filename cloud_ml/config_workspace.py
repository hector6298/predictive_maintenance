import os
import argparse

from azureml.core import Workspace
from azureml.core.compute import ComputeTarget, AmlCompute
from azureml.core.compute_target import ComputeTargetException


def create_compute(ws, cpu_cluster_name):
    # Verify that cluster does not exist already
    try:
        cpu_cluster = ComputeTarget(workspace=ws, name=cpu_cluster_name)
        print("Found existing cpu-cluster")
    except ComputeTargetException:
        print("Creating new cpu-cluster")
        
        # Specify the configuration for the new cluster
        compute_config = AmlCompute.provisioning_configuration(vm_size="STANDARD_D2_V2",
                                                            min_nodes=0,
                                                            max_nodes=4)

        # Create the cluster with the specified name and configuration
        cpu_cluster = ComputeTarget.create(ws, cpu_cluster_name, compute_config)
        
        # Wait for the cluster to complete, show the output log
        cpu_cluster.wait_for_completion(show_output=True)

if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('--resource-group', type=str,
                        dest='resource_group', help='Name of your Azure resource group')
    parser.add_argument('--azure-region', type=str,
                        dest='azure_region', help='Azure region where your services will be provisioned')
    parser.add_argument('--subscription-id', type=str,
                        dest='subscription_id', help='Azure subscription ID to provision your services')
    parser.add_argument('--aml-workspace', type=str,
                        dest='aml_workspace_name', help='Azure ML service workspace name')
    args = parser.parse_args()

    # Variables
    subscription_id = args.subscription_id
    resource_group = args.resource_group
    aml_workspace_name = args.aml_workspace_name
    azure_region = args.azure_region
    cpu_cluster_name = "cpu-cluster"


    # Create or load ML Workspace 
    ws = Workspace.create(subscription_id = args.subscription_id,
                    resource_group = args.resource_group,
                    name = args.aml_workspace_name,
                    location = args.azure_region,
                    exist_ok=True)
    print(f"Successsfully loaded workspace {args.aml_workspace_name}")

    # write the details of the workspace to a configuration file to the notebook library
    ws.write_config()
    print("Done writing workspace configuration")

    # Create the compute target if not exists
    create_compute(ws, cpu_cluster_name)