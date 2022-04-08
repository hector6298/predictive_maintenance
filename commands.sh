python cloud_ml/config_workspace.py \
    --subscription-id 56d25b97-81f8-4ce2-98a0-9be8f8c784f7 \
    --resource-group streaming_pdm \
    --azure-region eastus2 \
    --aml-workspace "predictive-maintenance-ml"

python cloud_ml/submit_train.py \
    --model-name "temp_model.pkl"

python cloud_ml/config_ml_module.py \
    --model-name "temp_model.pkl" \
    --image-name "temp_model"

$ACR_SERVER="1d755da8c1374569b501d2bc27f56c3c.azurecr.io"
$ACR_USERNAME="1d755da8c1374569b501d2bc27f56c3c"
$ACR_PASSWORD="2WS8ob+/HJGNHxWw+I707FhkAPUuIz02"



az login
az acr login --name 1d755da8c1374569b501d2bc27f56c3c --username $ACR_USERNAME --password $ACR_PASSWORD

cd modules/iot_edge/humid_telemetry/modules/ml_inference    

docker build -t aml/temp_model:latest \
             -t aml/temp_model:1 \
             -f "Dockerfile" .


docker tag aml/temp_model:latest ${ACR_SERVER}/aml/temp_model:latest 
docker push ${ACR_SERVER}/aml/temp_model:latest

cd modules/iot_edge/humid_telemetry/modules/send_telemetry
docker build -t aml/send_telemetry:latest \
             -t aml/send_telemetry:1 \
             -f "Dockerfile.arm32v7" .

docker tag aml/send_telemetry:latest ${ACR_SERVER}/aml/send_telemetry:latest 
docker push ${ACR_SERVER}/aml/send_telemetry:latest


python cloud_ml/config_deployment.py \
    --acr-server ${ACR_SERVER} \
    --acr-username ${ACR_USERNAME} \
    --acr-pass ${ACR_PASSWORD} \
    --telemetry-image ${ACR_SERVER}/aml/send_telemetry:latest \
    --inference-image ${ACR_SERVER}/aml/temp_model:latest 


!az iot edge set-modules --device-id $iot_device_id \
                         --hub-name $iot_hub_name \
                         --content deployment.json