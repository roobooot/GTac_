# -*- coding: utf-8 -*-
"""
Created on Fri Dec  4 11:23:56 2020

@author: Zeyu
"""

# import numpy as np
from data_gen import data_checkout
# import matplotlib.pyplot as plt
import serial
import time
import pandas as pd
import seaborn as sns
import argparse

COLUMNS = [ 'mat_x1y1','mat_x1y2','mat_x1y3','mat_x1y4',
            'mat_x2y1','mat_x2y2','mat_x2y3','mat_x2y4',
            'mat_x3y1','mat_x3y2','mat_x3y3','mat_x3y4',
            'mat_x4y1','mat_x4y2','mat_x4y3','mat_x4y4',
            'mag_x','mag_y','mag_z','motor_step','milliseconds'
            ]

if __name__ == '__main__':
    #current time
    timestr = time.strftime("%Y%m%d_%H%M%S")
    # parse the argumments
    parser = argparse.ArgumentParser()
    parser.add_argument("-sp", "--serialport",default='COM5',
                        help = "set serial port (default: COM5)")
    parser.add_argument("-l", "--locname",default='L5',
                        help = "set location name where probe pressing, L1-L9, (default: L5)")
    parser.add_argument("-p", "--datapoints",default=100,type=int,
                        help = "set number of data points to collect (default: 100)")
    # Read arguments from command line
    args = parser.parse_args()
    SerialPort,locname,DataPoints = args.serialport, args.locname, args.datapoints
    # creat a pandas DataFrame to store the data
    df = pd.DataFrame(columns=COLUMNS)
    # open the serial port
    ser = serial.Serial(SerialPort, 115200)
    time.sleep(1)
    if ser.is_open:
        print('Serial Port Opened:\n',ser)
        ser.flushInput()
    start = time.time()
    
    # Read and record the data
    n_trunck = 3 # how many repeated during readout (adjust in Arduino code)
    i = 0
    filename = 'data/'+locname+ '_' + str(DataPoints)+ '_points_' + timestr + '.csv'
    while(i<DataPoints):
        data = data_checkout(ser,n_trunck)
        flat_data = [val for sublist in data for val in sublist]
        ms = int(round((time.time()-start) * 1000))
        flat_data.append(ms)
        print('{}/{}:{}'.format(i,DataPoints,data)) # print what data read-out
        df.loc[len(df)] = flat_data # append data into dataframe
        i = i + 1
    end = time.time()
    print(end - start,' seconds')
    ser.close()
    print('Serial Port Closed')
    df.to_csv(filename)
    print('data saved:'+filename)
    # plotting the data
    