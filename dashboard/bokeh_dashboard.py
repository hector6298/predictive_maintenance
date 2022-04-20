
import numpy as np
import panel as pn

from bokeh.io import curdoc
from bokeh.models import ColumnDataSource, DatetimeTickFormatter, Select
from bokeh.layouts import layout
from bokeh.plotting import figure
from datetime import datetime
from math import radians

pn.extension('bokeh')
date_pattern = ["%Y-%m-%d\n%H:%M:%S"]
rng = np.random.default_rng(12345)


# This will be the container that will hold all the data
source1 = ColumnDataSource(dict(
    time=[], x=[], y=[], z=[]
))


# Create a figure object with proper time format
def get_line(col, source):
    p = figure(width=300, height=350, x_axis_type="datetime")
    p.line(x='time', y=col, alpha=0.2, line_width=3, color='navy', source=source)
    
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

def produce_data():
    return { 'x': [rng.random()], 'y': [rng.random()], 'z': [rng.random()], 'time': [datetime.now()]}

# We produce new data here, and use the selector to discriminate
def update():
    new_data = produce_data()
    source1.stream(new_data, rollover=10)
    
    p['x'].title.text = f"Streaming {select.value} data"
    p['y'].title.text = f"Streaming {select.value} data"
    p['z'].title.text = f"Streaming {select.value} data"

# Callback function for when selector is changed. Restarts the streaming
def update_inter(attrname, old, new):
    source1.data = dict(time=[], x=[], y=[], z=[])
    update()



# Create a graph for each sensor value (x, y, z)
p = {'x': get_line('x', source1),
      'y': get_line('y', source1),
      'z': get_line('z', source1)
     }


# Selection widget
options = [("D1", "Device 1"), ("D2", "Device 2"), ("D3", "Device 3")]
select = Select(title="Devices", value="D1", options=options)
select.on_change("value", update_inter)


bootstrap = pn.template.BootstrapTemplate(title="Streaming predictive maintenance")
bootstrap.sidebar.append(select)

bootstrap.main.append(
    pn.Row(
        pn.Card(p['x']),
        pn.Card(p['z']),
        pn.Card(p['y'])
    )
)

# Call the update function every 500 ms
curdoc().add_periodic_callback(update, 500)


# Make the layout servable by panel
bootstrap.servable()