#! /usr/bin/env python

import time
from matplotlib import pyplot as plt
import numpy as np
import serial
import pandas as pd
from serial_port_test import raw_data_byts_checkout_2
import copy
import collections


# sudo chmod 666 /dev/ttyACM0


class Gripper:

    def __init__(self, SerialPort, init=False, BaudRate=115200, buffer_size=6):  # port name, baudrate, timeout
        self.SerialPort = SerialPort
        self.BaudRate = BaudRate
        self.ser = self.connect_frame(self.SerialPort, self.BaudRate)
        self.init = init
        self.dt_list = []
        if init:
            self.init_motors()
        self.avg = self._init_GTac(DataPoints=200)
        self.start = time.time()
        self.buffer = collections.deque(maxlen=buffer_size)
        self.positions = np.zeros(8)

    def connect_frame(self, SerialPort='/COM3', BaudRate=115200):
        # s = serial.Serial('/dev/ttyACM0', BaudRate, timeout=0)    # for ubuntu 16
        s = serial.Serial(SerialPort, BaudRate, timeout=0)  # for windows
        time.sleep(0.5)
        if s.is_open:
            print('Serial Port Opened:\n', s)
            s.flushInput()
        return s

    def _init_GTac(self, DataPoints=400):
        dt_list = []
        i = 0
        while i < DataPoints:
            data = raw_data_byts_checkout_2(self.ser, verbose=False)
            dt_list.append(data)
            i = i + 1
        avg = np.array(dt_list).mean(axis=0, dtype=int)
        print('Initial values of GTac have been found:')
        print(avg)
        return avg

    def load_data(self, f_d=0):
        ms = int(round((time.time() - self.start) * 1000))
        data = raw_data_byts_checkout_2(self.ser, verbose=False)
        data[:-1] = np.subtract(data[:-1], self.avg[:-1])
        data.append(ms)
        self.buffer.append(data[:-10])  # only record the sensors' data, motor(8) + freq (1) + time (1) = 10
        data[:-10] = np.mean(self.buffer, axis=0, dtype=int)
        self.dt_list.append(data)

    def init_motors(self):
        self.ser.write(b'<>')
        print('Motors have been initialized')
        time.sleep(0.5)

    def move_frame(self, NOM, deg):
        cmd = '<' + str(NOM) + str(deg) + '>'
        cmd = bytes(cmd.encode('UTF-8'))
        self.ser.write(cmd)


if __name__ == "__main__":
    gripper = Gripper(SerialPort='/COM3', init=True)
    #  init position
    print('start move')
    # gripper.data_collection(step=200, goal=900, Data_Points=20, rotate=True)

    gripper.init_motors()
    gripper.ser.close()
    plt.show()
