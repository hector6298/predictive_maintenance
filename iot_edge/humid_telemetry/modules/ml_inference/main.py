import sys
import threading
import signal
import json
import uuid
import traceback

from joblib import load
from azure.iot.device import IoTHubModuleClient, Message

# global counters
RECEIVED_MESSAGES = 0

def create_client():

    def load_model():
        clf = load("models/temp_model.pkl")
        return clf

    def get_prediction_payload(telemetry_sample):
        temp = telemetry_sample['temperature']
        humid = telemetry_sample['humidity']

        prediction = clf.predict([[temp, humid]])
        log_proba = clf.predict_proba([[temp, humid]])
        
        return {"temperature": temp,
                "humidity": humid,
                "prediction": int(prediction[0]),
                "log_proba": float(max(log_proba[0]))}

    # define function for handling received messages
    def receive_message_handler(message):
        # NOTE: This function only handles messages sent to "input1".
        # Messages sent to other inputs or to the default will be discarded.
        global RECEIVED_MESSAGES
        if message.input_name == "telemetryInput":
            RECEIVED_MESSAGES += 1

            print("Message received on telemetryInput. Beginning prediction...")

            try:
                telemetry_sample = json.loads(message.data)
                prediction_str = json.dumps(get_prediction_payload(telemetry_sample))
                out_msg = Message(prediction_str)
                out_msg.message_id = uuid.uuid4()
            except Exception as e:
                print(e)
                print(traceback.format_exc())
                raise

            print( "    Data: <<{}>>".format(out_msg.data) )
            print( "    Properties: {}".format(out_msg.custom_properties))
            print( "    Total calls received: {}".format(RECEIVED_MESSAGES))

            print("Forwarding message to IoT Hub")
            client.send_message(message)
            print("Message successfully forwarded")
        else:
            print("Message received on unknown input: {}".format(message.input_name))
    
    print("Starting module. Creating client.")
    client = IoTHubModuleClient.create_from_edge_environment()
    print("Loading ML model")
    clf = load_model()
    print("Init message reception > ")
    try:
        # Set handler
        client.on_message_received = receive_message_handler
    except:
        # Cleanup
        client.shutdown()

    return client


def main():
    print ( "\nPython {}\n".format(sys.version) )
    print ( "IoT Hub Client for Python" )

    # Event indicating sample stop
    stop_event = threading.Event()

    # Define a signal handler that will indicate Edge termination of the Module
    def module_termination_handler(signal, frame):
        print ("IoTHubClient sample stopped")
        stop_event.set()

    # Attach the signal handler
    signal.signal(signal.SIGTERM, module_termination_handler)

    # Create the client
    client = create_client()

    try:
        # This will be triggered by Edge termination signal
        stop_event.wait()
    except Exception as e:
        print("Unexpected error %s " % e)
        raise
    finally:
        # Graceful exit
        print("Shutting down client")
        client.shutdown()

if __name__ == '__main__':
    main()