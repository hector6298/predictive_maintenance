import asyncio
import sys
import signal
import threading
import json
import adafruit_dht
import time
import uuid

from datetime import datetime
from azure.iot.device.aio import IoTHubModuleClient
from azure.iot.device import Message
from board import D17

date_pattern = "%Y-%m-%d\n%H:%M:%S"


# Event indicating client stop
stop_event = threading.Event()

dht_device = adafruit_dht.DHT11(D17)
def create_client():
    client = IoTHubModuleClient.create_from_edge_environment()
    return client


async def run_sample(client):

    # Send a filled out Message object
    async def send_test_message(i: int):
        try:
            # Read from the RPi sensor
            temperature = dht_device.temperature
            humidity = dht_device.humidity

            # Build sensor document
            telemetry_json = {
                "messageCount": i,
                "humidity": humidity,
                "temperature": temperature,
                "timestamp": datetime.now().strftime(date_pattern)
            }
            telemetry_str = json.dumps(telemetry_json)

            print("sending message #" + str(i) + '\n' + telemetry_str)

            msg = Message(telemetry_str)
            msg.message_id = uuid.uuid4()
            msg.correlation_id = "correlation-1234"

            await client.send_message_to_output(msg, "telemetryOutput")
            print("done sending message #" + str(i))
        except Exception as error:
            # Errors happen fairly often, DHT's are hard to read, just keep going
            print(error.args[0])
            time.sleep(2.0)
            pass

    message_count = 0

    while True:
        await send_test_message(message_count)
        message_count += 1
        await asyncio.sleep(1)


def main():
    if not sys.version >= "3.5.3":
        raise Exception( "The sample requires python 3.5.3+. Current version of Python: %s" % sys.version )
    print ( "IoT Hub Client for Python" )

    # NOTE: Client is implicitly connected due to the handler being set on it
    client = create_client()

    # Define a handler to cleanup when module is is terminated by Edge
    def module_termination_handler(signal, frame):
        print ("IoTHubClient sample stopped by Edge")
        stop_event.set()

    # Set the Edge termination handler
    signal.signal(signal.SIGTERM, module_termination_handler)

    # Run the sample
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(run_sample(client))
    except Exception as e:
        print("Unexpected error %s " % e)
        raise
    finally:
        print("Shutting down IoT Hub Client...")
        loop.run_until_complete(client.shutdown())
        loop.close()


if __name__ == "__main__":
    main()
