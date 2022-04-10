
import os
import argparse
import json


def configure_deployment(input_template_dir, output_deployment_dir):
    # Based on the deployment_template.json file, we insert necessary information.
    file = open(input_template_dir)
    contents = file.read()

    contents = contents.replace('__REGISTRY_SERVER_NAME', acr_login_server)
    contents = contents.replace('__REGISTRY_PASSWORD', acr_password)
    contents = contents.replace('__REGISTRY_USER_NAME', acr_name)
    contents = contents.replace('__REGISTRY_TELEMETRY_IMAGE_LOCATION', telimg_location)
    contents = contents.replace('__REGISTRY_ML_IMAGE_LOCATION', mlimg_location)
    contents = contents.replace('__CREATE_OPTIONS_INFERENCE', create_options_inference_str)
    contents = contents.replace('__CREATE_OPTIONS_TELEMETRY', create_options_telemetry_str)
    contents = contents.replace('__CREATE_OPTIONS_SYSTEM', create_option_systemModules)
    contents = contents.replace('__CREATE_OPTIONS_EDGEHUB', create_options_edgeHub)


    with open(output_deployment_dir, 'wt', encoding='utf-8') as output_file:
        output_file.write(contents)


if __name__ == "__main__":
    
    parser = argparse.ArgumentParser()
    parser.add_argument('--acr-server', type=str,
                        dest='acr_server', help='Azure Container Registry server URL')
    parser.add_argument('--acr-username', type=str,
                        dest='acr_username', help='Azure Container Registry username')
    parser.add_argument('--acr-pass', type=str,
                        dest='acr_pass', help='Azure Container Registry password')
    parser.add_argument('--telemetry-image', type=str,
                        dest='telemetry_image', help='Image name for telemetry module')
    parser.add_argument('--inference-image', type=str,
                        dest='inference_image', help='Image name for ML inference module')
    args = parser.parse_args()

    # Variables
    print("Preparing variables")
    acr_login_server = args.acr_server
    acr_password = args.acr_pass
    acr_name = args.acr_username
    telimg_location = args.telemetry_image
    mlimg_location = args.inference_image
    input_template_dir = 'iot_edge/humid_telemetry/deployment.template.json'
    output_deployment_dir = 'iot_edge/humid_telemetry/config/deployment.arm32v7.json'


    create_option_systemModules = {}

    create_options_edgeHub = {
        "HostConfig": {
            "PortBindings": {
            "5671/tcp": [
                {
                "HostPort": "5671"
                }
            ],
            "8883/tcp": [
                {
                "HostPort": "8883"
                }
            ],
            "443/tcp": [
                {
                "HostPort": "443"
                }
            ]
            }
        }
    }

    create_options_inference = {
        "HostConfig": {
            "Runtime":"nvidia",
            "PortBindings": {
            "5001/tcp": [{"HostPort":"5001"}]
            }
        }
    }

    create_options_telemetry =  {
            "HostConfig": {
                "Privileged": True,
                "Devices": [
                {
                    "PathOnHost": "/dev/gpiomem",
                    "PathInContainer": "/dev/gpiomem",
                    "CgroupPermissions": "rwm"
                }
            ]
        }
    }

    create_options_telemetry_str = str(json.dumps(json.dumps(create_options_telemetry)))   
    create_options_inference_str = str(json.dumps(json.dumps(create_options_inference)))
    create_options_edgeHub = str(json.dumps(json.dumps(create_options_edgeHub)))
    create_option_systemModules = str(json.dumps(json.dumps(create_option_systemModules)))

    configure_deployment(input_template_dir, output_deployment_dir)

    print("Done writing variables on deployment file")