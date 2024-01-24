#!/usr/bin/env python3

import platform
import logging
import asyncio
import struct
import csv
import time
import datetime

import matplotlib
import matplotlib.pyplot as plt
import numpy as np

from bleak import BleakClient
from bleak import BleakScanner
from bleak import _logger as logger

TARGET_NAME = "Progressor"

""" Progressor Commands """
CMD_TARE_SCALE = 100
CMD_START_WEIGHT_MEAS = 101
CMD_STOP_WEIGHT_MEAS = 102
CMD_START_PEAK_RFD_MEAS = 103
CMD_START_PEAK_RFD_MEAS_SERIES = 104
CMD_ADD_CALIBRATION_POINT = 105
CMD_SAVE_CALIBRATION = 106
CMD_GET_APP_VERSION = 107
CMD_GET_ERROR_INFORMATION = 108
CMD_CLR_ERROR_INFORMATION = 109
CMD_ENTER_SLEEP = 110
CMD_GET_BATTERY_VOLTAGE = 111

""" Progressor response codes """
RES_CMD_RESPONSE = 0
RES_WEIGHT_MEAS = 1
RES_RFD_PEAK = 2
RES_RFD_PEAK_SERIES = 3
RES_LOW_PWR_WARNING = 4

def welcome_msg():
    msg = """

                                                                                                                                                              
                .@@%            &@@*                      @@@.          %&&,                                    .@@@                                          
               /@@@@#         .&@@@@,                     @@@.                                                  .@@@                                          
              #@@@@@@@.      ,@@@@@@@/                    @@@&*...      ...       ..........             .....  .@@@         ........             ........... 
             &@@@. (@@@/    .@@@/ ,@@@&                   @@@@@@@@,     &@@,     /@@@@@@@@@@@@#       .@@@@@@@, .@@@       @@@@@@@@@@@@*       (@@@@@@@@@@@@% 
            &@@&.   #@@@*  (@@@/    @@@%                  @@@%.         &@@,     (@@@(     ,@@@&     ,@@@%      .@@@      &@@&,     (@@@/     #@@@/     .@@@% 
          .&@@&      ,@%  (@@@.      @@@@                 @@@.          &@@,     (@@%       %@@&     ,@@&.      .@@@      &@@,       %@@/     %@@&       (@@% 
         .@@@(           &@@@.        %@@@,               @@@.          &@@,     (@@%       %@@&     ,@@&.      .@@@      &@@,       &@@/     %@@&       (@@% 
        *@@@#           %@@@,          %@@@,              @@@.          &@@,     (@@%       %@@&     ,@@&.      .@@@      &@@, .&@@@@@@&.     %@@&       (@@% 
       (@@@/          ,&@@&             ,@@@/             @@@.          &@@,     (@@%       %@@&     ,@@&.      .@@@      &@@,  ......        %@@&       (@@% 
      &@@@.          .@@@/               ,@@@%            @@@.          &@@,     (@@%       %@@&     ,@@&.      .@@@      &@@,                %@@&       (@@% 
     &@@&.          /@@@(                  @@@%           @@@.          &@@,     (@@%       %@@&     ,@@&.      .@@@      &@@,       .//,     %@@&       (@@% 
   .&@@@           /@@@(                    @@@@          @@@.          &@@,     (@@%       %@@&     ,@@@.      .@@@      &@@*       *@@(     %@@@       (@@% 
  .@@@@@&&&&&&&&&&@@@@,  &&&&&&&&&&&&&&&&&&&@@@@@         @@@@@&&&,     &@@,     (@@%       %@@&      %@@@@&&&&@@@@@      (@@@@&&&&&@@@@.     *@@@@&&&&  (@@% 
 *@@@@@@@@@@@@@@@@@@@,  &@@@@@@@@@@@@@@@@@@@@@@@@@,       ,%@@@@@@,     &@@,     (@@%       %@@&       ,&@@@@@@@@@@@       .#@@@@@@@@@/         (&@@@@@  (@@%
                                                                                                                                                         (@@% 
                                                                                                                                                         (@@% 
                                                                                                                                                         (@@% 
        """
    print("{0}".format(msg))


welcome_msg()


progressor_uuids = {
    "7e4e1701-1ea6-40c9-9dcc-13d34ffead57": "Progressor Service",
    "7e4e1702-1ea6-40c9-9dcc-13d34ffead57": "Data",
    "7e4e1703-1ea6-40c9-9dcc-13d34ffead57": "Control point",
}

progressor_uuids = {v: k for k, v in progressor_uuids.items()}

PROGRESSOR_SERVICE_UUID = "{}".format(
    progressor_uuids.get("Progressor Service")
)
DATA_CHAR_UUID = "{}".format(
    progressor_uuids.get("Data")
)
CTRL_POINT_CHAR_UUID = "{}".format(
    progressor_uuids.get("Control point")
)

csv_filename = None
csv_tags = {"weight" : None,
            "time" : None}


current_cmd_request = None


def plot_measurments():
    global csv_filename

    time = []
    weight = []

    if csv_filename is not None:
        with open(csv_filename, 'r') as csvfile:
            plots = csv.reader(csvfile, delimiter=',')
            for row in plots:
                try:
                    time.append(float(row[1]) / float(1000000.0))
                    weight.append(float(row[0]))
                except Exception as e:
                    pass
        plt.plot(time, weight)
        plt.xlabel('Time [S]')
        plt.ylabel('Weight [Kg]')
        plt.title('Measurements')
        plt.grid()
        plt.show()   

def csv_create():

    ts = time.time()
    global csv_filename
    csv_filename = "measurements_" + \
        datetime.datetime.fromtimestamp(
            ts).strftime('%Y-%m-%d_%H-%M-%S')+'.csv'
    with open(csv_filename, 'a', newline='') as csvfile:
        logwrite = csv.DictWriter(csvfile, csv_tags.keys())
        logwrite.writeheader()


def csv_write(value, useconds):
    global csv_filename

    csv_tags['weight'] = "{0:.1f}".format(value)
    csv_tags['time'] = useconds
    print(csv_tags)
    try:
        with open(csv_filename, 'a', newline='') as csvfile:
            logwrite = csv.DictWriter(csvfile, csv_tags.keys())
            logwrite.writerow(csv_tags)
    except Exception as e:
        print(e)


def notification_handler(sender, data):
    """ Function for handling data from the Progressor """
    global current_cmd_request
    try:
        if data[0] == RES_WEIGHT_MEAS:
            print("Payload size : {0}".format(data[1]))

            value = [data[i:i+4] for i in range (2, len(data), 8)]
            timestamp = [data[i:i+4] for i in range (6, len(data), 8)]
            # Log measurements to csv file
            for x, y in zip(value,timestamp):
                weight, = struct.unpack('<f', x)
                useconds, = struct.unpack('<I', y)
                csv_write(weight, useconds)
        elif data[0] == RES_LOW_PWR_WARNING:
            print("Received low battery warning.")
        elif data[0] == RES_CMD_RESPONSE:
            if current_cmd_request == CMD_GET_APP_VERSION:
                print("---Device information---")
                print("FW version : {0}".format(data[2:].decode("utf-8")))
            elif current_cmd_request == CMD_GET_BATTERY_VOLTAGE:
                vdd, = struct.unpack('<I', data[2:]) 
                print("Battery voltage : {0} [mV]".format(vdd))
            elif current_cmd_request == CMD_GET_ERROR_INFORMATION:
                try:
                    print("Crashlog : {0}".format(data[2:].decode("utf-8")))
                    print("------------------------")
                except:
                    print("Empty crashlog")
                    print("------------------------")
    except Exception as e:
        print(e)


async def run(loop, debug=False):
    
    global current_cmd_request

    if debug:
        import sys

        # loop.set_debug(True)
        #l = logging.getLogger("bleak")
        # l.setLevel(logging.DEBUG)
        #h = logging.StreamHandler(sys.stdout)
        # h.setLevel(logging.DEBUG)
        # l.addHandler(h)

    scanner = BleakScanner()
    devices = await scanner.discover(timeout=10)
    for d in devices:
        if d.name[:len(TARGET_NAME)] == TARGET_NAME:
            address = d.address
            print("Found \"{0}\" with address {1}".format(d.name, d.address))
            break

    async with BleakClient(address) as client:
        x = await client.is_connected()
        csv_create()
        print("Connected: {0}".format(x))

        await client.start_notify(DATA_CHAR_UUID, notification_handler)
        current_cmd_request = CMD_GET_APP_VERSION
        await client.write_gatt_char(CTRL_POINT_CHAR_UUID, bytearray([CMD_GET_APP_VERSION]), response=True)
        await asyncio.sleep(.5)
        current_cmd_request = CMD_GET_BATTERY_VOLTAGE
        await client.write_gatt_char(CTRL_POINT_CHAR_UUID, bytearray([CMD_GET_BATTERY_VOLTAGE]), response=True)
        await asyncio.sleep(.5)
        current_cmd_request = CMD_GET_ERROR_INFORMATION
        await client.write_gatt_char(CTRL_POINT_CHAR_UUID, bytearray([CMD_GET_ERROR_INFORMATION]), response=True)
        await asyncio.sleep(.5)
        await client.write_gatt_char(CTRL_POINT_CHAR_UUID, bytearray([CMD_START_WEIGHT_MEAS]), response=True)
        await asyncio.sleep(10)
        await client.write_gatt_char(CTRL_POINT_CHAR_UUID, bytearray([CMD_ENTER_SLEEP]))


if __name__ == "__main__":

    loop = asyncio.get_event_loop()
    loop.run_until_complete(run(loop, False))
    plot_measurments()
