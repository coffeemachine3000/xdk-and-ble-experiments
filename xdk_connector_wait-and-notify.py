"""
Connect via Bluetooth Low Energy to the Bosch XDK and receive sensor data.

Requires a BGAPI-compatible Bluetooth Dongle like the BlueGiga BLED112. On the XDK, the SendAccelerometerDataOverBle firmware must be running.
"""

import csv
from datetime import datetime
import logging
import threading
import time

import pygatt

logging.basicConfig()
logging.getLogger('pygatt').setLevel(logging.DEBUG)

values = []

current_time = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
filename = "logAccel_" + current_time + ".csv"
csv_file = open(filename, mode='w', newline='')
csv_writer = csv.writer(csv_file, delimiter=';')
unit_descriptions = ("timestamp", "bma280_x[mg]", "bma280_y[mg]", "bma280_z[mg]")
csv_writer.writerow(unit_descriptions)

conditon_var = threading.Condition()

def handle_data(handle, raw_value):
    """Callback function: decode and save the raw values coming in from the handle."""
    global values
    # decode raw values, get rid of null bytes and
    # split along spaces to get a list for writing into csv later:
    values = raw_value.decode().replace('\x00', '').split(' ')
    timeString = datetime.utcnow().strftime("%Y%m%d_%H%M%S.%f")
    values.insert(0, timeString)
    with conditon_var:
        csv_writer.writerow(values)
        conditon_var.notify()

adapter = pygatt.BGAPIBackend()

try:
    adapter.start()
    device = adapter.connect('FC:D6:BD:10:2B:04', interval_min=10, interval_max=15, latency=0)
    # send "start" command to the XDK:
    device.char_write("0c68d100-266f-11e6-b388-0002a5d5c51b", bytearray("start", encoding="utf-8"), wait_for_response=False)
    # subscribe to get notifications; set callback to our function handle_data above:
    device.subscribe("1ed9e2c0-266f-11e6-850b-0002a5d5c51b", callback=handle_data, indication=False)
    # use condition object from threading module to wait:
    with conditon_var:
        while True:
            conditon_var.wait()
finally:
    adapter.stop()
