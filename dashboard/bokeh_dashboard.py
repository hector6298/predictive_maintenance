import os
import numpy as np
import sys
import panel as pn
import time
import logging
import threading
import argparse

from azure.eventhub import EventHubConsumerClient
from bokeh.io import curdoc
from bokeh.models import ColumnDataSource, DatetimeTickFormatter, Select
from bokeh.layouts import layout
from bokeh.plotting import figure
from datetime import datetime
from math import radians
from tornado import gen
from functools import partial

pn.extension()
logger = logging.getLogger("azure.eventhub")
logging.basicConfig(level=logging.WARNING)

parser = argparse.ArgumentParser()
parser.add_argument('--iothub-conn-str', type=str,
                    dest='iothub_connection_string', help='The built-in compatible endpoint from your IoT Hub')
parser.add_argument('--iothub-consumer-group', type=str,
                        dest='iothub_consumer_group', help='The endpoint consumer group')
parser.add_argument('--iothub-name', type=str,
                        dest='iothub_name', help='The IoT Hub compatible name')
args = parser.parse_args()

# Global variables
RECEIVED_MESSAGES = 0
date_pattern = "%Y-%m-%d\n%H:%M:%S"
connection_str = args.iothub_connection_string
consumer_group = args.iothub_consumer_group
eventhub_name = args.iothub_name

# This will be the container that will hold all the data
source1 = ColumnDataSource(dict(
    timestamp=[], temperature=[], humidity=[]
))

# Instantiate the Event Hub client to get telemetry
client = EventHubConsumerClient.from_connection_string(connection_str, 
                                                    consumer_group, 
                                                  eventhub_name=eventhub_name)

# Current Bokeh Document
doc = curdoc()


# Create a figure object with proper time format
def get_line(col, source):
    p = figure(width=300, height=350, x_axis_type="datetime")
    p.line(x='timestamp', y=col, alpha=0.2, line_width=3, color='navy', source=source)
    
    p.xaxis.formatter = DatetimeTickFormatter(
        seconds=date_pattern,
        minsec=date_pattern,
        minutes=date_pattern,
        hourmin=date_pattern,
        hours=date_pattern,
        days=date_pattern,
        months=date_pattern,
        years=date_pattern
    )
    p.xaxis.major_label_orientation=radians(80)
    
    p.xaxis.axis_label = "Date"
    p.yaxis.axis_label = "Value"
    
    return p


@gen.coroutine
def update_stream(stream_point):
    source1.stream(stream_point, rollover=10)


# We produce new data here, and use the selector to discriminate
def message_handler(partition_context, event):
    global RECEIVED_MESSAGES
    global source1
    global p 
    global client
    
    RECEIVED_MESSAGES += 1

    if not threading.main_thread().is_alive():
        client.close()
        sys.exit(0)

    logger.info("Received event from partition {}".format(partition_context.partition_id))
    partition_context.update_checkpoint(event)

    message = event.body_as_json()

    print("\nMessage received:")
    print( "    Data: <<{}>>".format(message) )

    #data = json.loads(message)
    
    stream_point = {
        'timestamp': [datetime.strptime(message['timestamp'], date_pattern)],
        'temperature': [message['temperature']],
        'humidity': [message['humidity']]
    }
    
    doc.add_next_tick_callback(partial(update_stream, stream_point=stream_point))
    
    time.sleep(1)

# Callback in the event of errors on the Event Hub client
def on_error(partition_context, error):
    if partition_context:
        print("An exception: {} occurred during receiving from Partition: {}.".format(
            partition_context.partition_id,
            error
        ))
    else:
        print("An exception: {} occurred during the load balance process.".format(error))
        
        
# Callback function for when selector is changed. Restarts the streaming
def selector_update(attrname, old, new):
    source1.data = dict(timestamp=[], 
                        temperature=[], 
                        humidity=[], 
                        )

    p['temperature'].title.text = f"Streaming {select.value} data"
    p['humidity'].title.text = f"Streaming {select.value} data"
    
# We will begin listening to telemetry on a separate thread
def hub_task():
    print("Initializing message reception")
    with client:
        client.receive(
            on_event=message_handler,
            on_error=on_error,
            starting_position="-1",  # "-1" is from the beginning of the partition.
        )

# Watcher that will shutdown the client before closing the application
def client_watcher():
    while threading.main_thread().is_alive():
        time.sleep(0.1)
    else:
        print("Shutting down Event Hub client")
        client.close()


###########################
# Dashboard configuration #
###########################

# Selection widget
options = [("D1", "Device 1"), ("D2", "Device 2"), ("D3", "Device 3")]
select = Select(title="Devices", value="D1", options=options)
select.on_change("value", selector_update)

# Create a graph for each sensor value (temperature, humidity)
p = {'temperature': get_line('temperature', source1),
      'humidity': get_line('humidity', source1),
    }

# Get a bootstrap template to style the dashboard
bootstrap = pn.template.BootstrapTemplate(title="Streaming predictive maintenance")
bootstrap.sidebar.append(select)

# Layout of the dashboard
bootstrap.main.append(
    pn.Row(
        pn.Card(p['temperature']),
        pn.Card(p['humidity'])
    )
)

bootstrap.servable()

# Executing the data and watcher threads
watcher_thread = threading.Thread(target=client_watcher)
data_thread = threading.Thread(target=hub_task)
data_thread.start()
watcher_thread.start()

