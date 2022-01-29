# -*- coding: utf-8 -*-
"""
Created on Fri Apr  9 09:50:42 2021

@author: Zeyu
"""

import serial
import time
from data_gen import data_checkout,raw_data_checkout

if __name__ == '__main__':
    try:
        ser = serial.Serial('COM12', 115200)
    except:
        print('Serial Connection Failed, Will Try Again in 3 SECONDS')
        time.sleep(3)
    else:
        if ser.is_open:
            print('Serial Port Opened:\n',ser)
            ser.flushInput()
    while(1):

            try:
                data = raw_data_checkout(ser)
                print('data:',data) # print what data read-out
                # if len(data)!=9:
                #     raise Exception('Sorry, wrong data size')
            except:
                print('data reading out is wrong')