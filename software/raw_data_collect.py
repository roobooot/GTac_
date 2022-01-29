# -*- coding: utf-8 -*-
"""
Created on Mon Dec 28 13:39:54 2020

@author: Zeyu
"""

from data_gen import raw_data_checkout
# import numpy as np
# import matplotlib.pyplot as plt
import serial
import time
import pandas as pd
import seaborn as sns
import argparse
import os

COLUMNS = ['col',
           'row1','row2','row3','row4',
           'mag_x','mag_y','mag_z',
           'motor_step','milliseconds']

if __name__ == '__main__':
    #current time
    timestr = time.strftime("%Y%m%d_%H%M%S")
    datestr = time.strftime("%Y%m%d")
    # parse the argumments
    parser = argparse.ArgumentParser()
    parser.add_argument("-sp", "--serialport",default='COM5',
                        help = "set serial port (default: COM5)")
    parser.add_argument("-l", "--locname",default='Test',
                        help = "set location name where probe pressing, L1-L9, (default: L5)")
    parser.add_argument("-p", "--datapoints",default=100,type=int,
                        help = "set number of data points to collect (default: 100)")
    # Read arguments from command line
    args = parser.parse_args()
    SerialPort,locname,DataPoints = args.serialport, args.locname, args.datapoints
    # creat a pandas DataFrame to store the data
    df = pd.DataFrame(columns=COLUMNS)
    
    i = 0
    outdir = os.path.join('./data', datestr)
    if not os.path.exists(outdir):
        os.mkdir(outdir)
    csvname = 'GTAC_raw_'+locname+ '_' + str(DataPoints)+ '_points_' + timestr + '.csv'
    filename = os.path.join(outdir, csvname)
    while(1):
        try:
            ser = serial.Serial('COM5', 115200)
        except:
            print('Serial Connection Failed, Will Try Again in 3 SECONDS')
            time.sleep(3)
        else:
            if ser.is_open:
                print('Serial Port Opened:\n',ser)
                ser.flushInput()
            # Read and record the data
            i = 0
            start = time.time()
            
            while(i<DataPoints):
                try:
                    data = raw_data_checkout(ser)
                    print('data:',data) # print what data read-out
                    if len(data)!=9:
                        raise Exception('Sorry, wrong data size')
                        continue
                except:
                    print('data reading out is wrong')
                    continue
                ms = int(round((time.time()-start) * 1000))
                data.append(ms)
                print('{}/{}:{}'.format(i+1,DataPoints,data)) # print what data read-out
                df.loc[len(df)] = data # append data into dataframe
                i = i + 1
            end = time.time()
            print(end - start,' seconds')
            ser.close()
            print('Serial Port Closed')
            df.to_csv(filename)
            print('data saved:'+filename)
            break